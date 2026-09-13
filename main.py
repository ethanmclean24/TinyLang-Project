from config import LANGUAGE_NAME, AUTHOR, VERSION, DESCRIPTION

def main():
    print(f"Welcome to {LANGUAGE_NAME} Version {VERSION}")
    print(DESCRIPTION)
    print(f"Designed by: {AUTHOR}")
    print("\nMilestone 1 status: language specification in progress.")
    print("Later implementation components remain intentionally inactive.")

if __name__ == "__main__":
    main()
