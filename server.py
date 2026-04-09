import fastf1
import os
import sys
import logging
from fastf1.ergast import Ergast
from mcp.server.fastmcp import FastMCP

# 1. Logging Configuration: Setting up logging for debugging and monitoring
logging.basicConfig(
    filename='f1_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# caching to solve data efficiency problem
# problem:  F1 telemetry datasets are massive (gigabytes).
# How do we prevent our server from taking 5 minutes to answer a single question?
if not os.path.exists('f1_cache'):
    os.mkdir('f1_cache')
fastf1.Cache.enable_cache('f1_cache')

# Create a MCP server, a bridge
mcp = FastMCP("F1_Server")
ergast = Ergast()

# 3. Tool Definition: Generating the JSON Schema menu
# so creating JSON Schema is done by this MCP tool. it create a JSON schema for this and send it to LLM
@mcp.tool()
def get_race_results(year: int,event_name: str, session_type: str = 'R') -> str:
    """
        Fetches the final classification results for a specific Formula 1 session.

        Args:
            year: The championship year (e.g., 2023).
            event_name: The name or location of the race (e.g., 'Monza', 'Italian Grand Prix').
            session_type: The session identifier ('R' for Race, 'Q' for Qualifying, 'FP1' for Practice). Defaults to 'R'.
        """
    try:
        # fetch the data
        session = fastf1.get_session(year, event_name, session_type)

        # load the data(skipping the telemetry and weather data to save time)
        session.load(telemetry=False, weather=False)

        results = session.results

        logging.info(f"Raw dataframe {results.columns}")
        logging.info("\n" + str(results.head(5)))


        # C. Serialization: Packaging data for the LLM
        # Convert the results DataFrame to a JSON string
        summary = f"Result for {year} {event_name} - session {session_type}\n"
        summary += "-" *40 + "\n"

        for index,row in results.iterrows():
            # FastF1 result columns are capitalized (e.g., 'Position').
            pos = str(row['Position']).replace('.0', '')
            driver = row['FullName'] # HAM, LEC....
            team = row['TeamName']
            status = row['Status']

            summary += f"{pos}. {driver} ({team}) - {status}\n"
        logging.info(f"The thing that is passed to the llm is the following: ✅\n" + summary)
        return summary

    except Exception as e:
        logging.exception("Failed while building race results summary")
        return f"Error fetching F1 data: {str(e)}"


@mcp.tool()
def get_season_standings(year: int) -> str:
    """
    Fetches the World Championship Driver Standings for an entire Formula 1 season.
    Use this ONLY when the user asks about the 'championship', 'entire season', or 'season winner'.
    """
    try:
        logging.info(f"--- Fetching Championship Standings for {year} ---")

        # Ergast fetches the entire season's points
        standings = ergast.get_driver_standings(season=year)

        # Extract the actual dataframe from the Ergast response
        df = standings.content[0]

        summary = f"Formula 1 World Championship Standings for {year}\n"
        summary += "-" * 40 + "\n"

        for index, row in df.iterrows():
            pos = row['position']
            # Ergast provides first and last names separately
            driver = f"{row['givenName']} {row['familyName']}"
            points = row['points']

            summary += f"{pos}. {driver} - {points} points\n"

        logging.info(" FINAL CHAMPIONSHIP STRING:\n" + summary)
        return summary

    except Exception as e:
        logging.error(f" Error fetching championship data: {str(e)}")
        return f"Error fetching championship data: {str(e)}"


# 4. Server Execution: Starting the MCP server
if __name__ == '__main__':
    if len(sys.argv) > 1 and (sys.argv[1]) == 'test':
        #we manually run and put manual parameters
        #But we do fetech the data from fastF1 and check if that work too
        test_output = get_race_results(2023, 'Monza', 'R')
        print(f"The final race result is \t{test_output}")

    else:
        mcp.run(transport='stdio')

