import app1  
import app2  


def main():
    print("")
    print("Welcome to the Multi-Agent Chat Application!, which includes two agents: 'ben' (routes) and 'june' (concerts)?")
    print("")
    shared_history = []

    current_agent = (
        input(
            "Select initial agent ('ben': routes, 'june': concerts, 'exit':"
            " quit): "
        )
        .strip()
        .lower()
    )

    while True:
        if current_agent == "ben":
            current_agent = app2.run_chat(shared_history)

        elif current_agent == "june":
            current_agent = app1.run_chat(shared_history)

        elif current_agent in ["switch", "menu"]:
            current_agent = (
                input("\nChoose agent ('ben' or 'june'): ").strip().lower()
            )

        elif current_agent == "exit":
            print("\nExiting application. Goodbye!")
            break

        else:
            current_agent = (
                input("Invalid option. Please enter 'ben', 'june', or 'exit': ")
                .strip()
                .lower()
            )


if __name__ == "__main__":
    main()