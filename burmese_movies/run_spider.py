import subprocess
import os
from datetime import datetime

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.environ["SCRAPY_RUN_TIMESTAMP"] = timestamp
    output_dir = os.path.join("output", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    crawler_log = os.path.join(output_dir, f"crawler_output_{timestamp}.log")

    # Only LOG_FILE is passed dynamically here
    command = [
        "scrapy", "crawl", "movies",
        "-s", f"LOG_FILE={crawler_log}",
    ]

    print(f"Running crawler... Output will be saved to {output_dir}")
    subprocess.run(command)

if __name__ == "__main__":
    main()
