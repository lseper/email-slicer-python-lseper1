def slice_email(email: str) -> tuple[str, str]:
    if email.find("@") == -1:
        raise ValueError("no '@' found in email")

    username = email[:email.index("@")]     # username value = from 0 to index < @
    domain = email[email.index("@") + 1:]   # domain value = from index > @ to end
    return username, domain


if __name__ == "__main__":
    print("Please enter your Email Id:")
    email = input().strip()

    try:
        username, domain = slice_email(email)
        print("Your username is: ", username)
        print("Your domain is: ", domain)
    except ValueError:
        print("Please enter a valid Email Id.")
