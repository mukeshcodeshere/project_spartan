import os

def get_user_credentials():
    """Prompt the user to input their server and password."""
    server = input("Enter the username: ")
    password = input("Enter the password: ")
    # print(server)
    # print(password)
    return server, password

def create_or_update_env_file(server, password):
    """Create or update the .env file with the provided credentials."""
    env_content = f"USERNAME_LOGIN={server}\nPASSWORD_LOGIN={password}\n"
    
    # Write the credentials to the .env file
    with open("credential.env", "w") as f:
        f.write(env_content)
    print(".env file has been created/updated with the provided credentials.")

def delete_env_file():
    """Delete the .env file."""
    if os.path.exists("credential.env"):
        os.remove("credential.env")
        print(".env file has been deleted.")

def login():
    """Perform the login process using user input credentials and return a successful login flag."""
    successful_login = False
    
    while not successful_login:
        server, password = get_user_credentials()

        # Create or update the .env file with the user credentials
        create_or_update_env_file(server, password)

        # Importing the necessary function after environment variables are set
        from gcc_sparta_lib import test_auth_data_pull

        # Attempt to pull data and check if the login is successful
        login_status = test_auth_data_pull()

        if login_status == "successful_login":
            print("Login successful!")
            successful_login = True  # Set the flag to True if login is successful
        else:
            print("Login failed. Please check your credentials and try again.")
            delete_env_file()  # Delete the .env file if login fails
    
    return successful_login  # Return the flag indicating success
