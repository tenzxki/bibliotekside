from db_conn import get_connection

def main():
    try:
        mydb = get_connection()
        print("Kobling til databasen fungerer!")
        mydb.close()
    except Exception as e:
        print("Feil:", e)

if __name__ == "__main__":
    main()
