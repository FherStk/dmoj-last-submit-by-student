import requests

STUDENTS = [
    "username1",
    "username2",
    "..."
]

def get_submit_data_by_user(user):
    url = f"https://dmoj.elpuig.xeill.net/api/v2/submissions?user={user}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            content = response.json()
            submits = content.get("data", {}).get("objects", [])

            if not submits: return {
                "total": 0,
                "last": None,
                "error": None
            }

            dates = [submit['date'] for submit in submits if submit['date'] is not None]
            return {
                "total": len(submits),
                "last": max(dates),
                "error": None
            }

        else:
            return {
                "total": 0,
                "last": None,
                "error": response.status_code
            }

    except requests.exceptions.RequestException as e:
        return {
            "total": 0,
            "last": None,
            "error": e
        }

if __name__ == "__main__":
    print("Requesting data for the suplied students. The output will be formated in order to copy/paste into a spreadsheet.\n")
    print("USER\tTOTAL\tLAST")

    for user in STUDENTS:
        data = get_submit_data_by_user(user)
        print(f"{user}\t"
              f"{data["total"]}\t"
              f"{"Never" if data["last"] is None else data["last"][:19].replace("T", " ")}"
              f"{"\t" if data["error"] is not None else ""}"
              f"{data["error"] if data["error"] is not None else ""}")

    print("\nDONE")