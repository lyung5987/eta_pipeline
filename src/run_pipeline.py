from extract import run as extract_run
from transform import transform, latest_raw
from validate import run_checks, can_load
from load import run as load_run
import sys

def main():
    extract_run()
    path = latest_raw()
    df = transform(path)
    results = run_checks(df)
    if(can_load(results)):
        load_run(df, results, path)
    else:
        print("Validation failed, not loading")
        sys.exit(1)

if __name__ == "__main__":
    main()

