# Prosjektbeskrivelse og  dokumentasjon

## Bibliotekutlån

---

## 1. Prosjektidé og problemstilling

### Beskrivelse
Jeg skal lage en nettbasert bibliotekside hvor man logger inn og kan låne bøker fra en katalog. Brukeren sender en forespørsel om å låne en bok, og en administrator må godkjenne eller avslå forespørselen. Brukeren kan selv returnere en bok de har lånt, og admin kan også markere bøker som returnert. Når man logger inn blir man automatisk sendt til enten brukersiden eller adminsiden basert på hvilken rolle kontoen har. 

## Hva skal jeg gjøre på Eksamensdagen

På eksamensdagen skal jeg
- Lage et fungerende biblioteksystem som beskrevet ovenfor.
- Implementere sikkerhet med sessions, bcrypt og .env-fil
- Vise kunnskap om SSH og Debian WSL for sensor
- Bruke Kanban til prosjektstyring
- Opprette tabeller, koble til databasen og legge til alle ruter
- Login som redirecter bruker til riktig side basert på rolle.

- https://github.com/users/tenzxki/projects/2

---
## 2. Systembeskrivelse

**Formål med applikasjonen:**\
*Jeg ønsker å oppnå et simpelt men effektivt bibliotek system hvor bare ved et klikk kan du få tilgang til en bok. For å få bedre oversikt og sikkerhet har jeg valgt at brukeren må sende en forespørsel om å låne boka fremfor å bare trykke på lån og få den.*

**Brukerflyt:**\
*Du åpner siden og får opp innloggingssiden. Du logger inn og kommer frem til en katalog med tilgjengelige bøker. Du velger en bok og sender en låneforespørsel. Admin godkjenner forespørselen og setter en forfallsdato. Boken tilhører deg frem til du returnerer den. Du returnerer boken selv via "Mine lån"-siden, eller admin markerer den som returnert*

**Teknologier brukt:**

-  Python / Flask\
-  MariaDB\ MYSQL
-  HTML / CSS / JS\
-  Waitress

------------------------------------------------------------------------

## 3. Server-, infrastruktur- og nettverksoppsett

### Servermiljø

*Applikasjonen kjøres lokalt på Windows via Debian WSL. MariaDB er installert og kjører inne i Debian. Flask applikasjonen serveres med Waitress på port 8080.*

### Nettverksoppsett

-   IP-adresser\ localhost
-   Porter\ 8080
-   Brannmurregler (Ingen fordi alt er lokalt)

    Klient → Waitress → MariaDB  → Flask app

  - Waitress tar imot forespørselen fra nettleseren og sender den videre til flask.
  - Flask behandler forespørselen, kjører koden din, og spør MariaDB om data.
  - MariaDB svarer med data tilbake til Flask.
  - Flask lager HTML-svaret og sender det tilbake gjennom Waitress til nettleseren. 
    

### Tjenestekonfigurasjon

-   MariaDB startes med: sudo mariadb -u root -p
-   Applikasjonen startes med: python run.py
-   Waitress kjører på host 0.0.0.0 og port 8080
-   Miljøvariabler lagres i .env fil og leses med python-dotenv

------------------------------------------------------------------------

## 4. Prosjektstyring -- GitHub Projects (Kanban)

- Sett opp projektstruktur (Sette opp filer og mapper)
- Installerer pakker i venv
- Opprette database og tabeller
- Lage db_conn.py (Leser DB info fra .env)
- .env og config
- Login og logout
- Admin : se alle lån
- Admin : godkjenn forespørsel
- Admin : avslå forespørsel
- Admin : marker som returnert
- Bruker: Katalog
- Bruker : Send låneforespørsel
- Bruker : mine lån
- Bruker : returner bok
- Frontend
- run.py og Waitress


Kanban-boardet ga god oversikt over hva som var gjort og hva som gjenstod.

------------------------------------------------------------------------

## 5. Databasebeskrivelse

**library_db**

**Tabeller:**\
+----+-------+---------------+----------+-------+
| id | name  | email         | password | role  |
+----+-------+---------------+----------+-------+
|  1 | Admin | admin@lib.com | $2b$12$… | admin |
|  2 | Sarah | sarah@epost.no| $2b$12$… | user  |
|  3 | Mark  | mark@epost.no | $2b$12$… | user  |
+----+-------+---------------+----------+-------+

+----+------------+---------+-----------+
| id | title      | author  | genre     |
+----+------------+---------+-----------+
|  1 | Bok En     | Forfatter A | Sci-Fi |
|  2 | Bok To     | Forfatter B | Fantasy|
|  3 | Bok Tre    | Forfatter C | Drama  |
+----+------------+---------+-----------+

+----+---------+---------+---------+-------------+------------+-------------+
| id | book_id | user_id | status  | borrowed_at | due_date   | returned_at |
+----+---------+---------+---------+-------------+------------+-------------+
|  1 |       1 |       2 | active  | 2026-05-01  | 2026-06-01 | NULL        |
|  2 |       2 |       3 | pending | NULL        | NULL       | NULL        |
|  3 |       3 |       2 | returned| 2026-03-01  | 2026-04-01 | 2026-03-28  |
+----+---------+---------+---------+-------------+------------+-------------+


**SQL-eksempel:**

``` sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    genre VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE borrowings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    status ENUM('pending', 'active', 'returned') DEFAULT 'pending',
    borrowed_at DATE DEFAULT NULL,
    due_date DATE DEFAULT NULL,
    returned_at DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

```
**Relasjoner**
users --< borrowings >-- books
En bruker kan ha mange borrowings. En bok kan ha mange borrowings over tid, men bare en aktiv om gangen.

------------------------------------------------------------------------

## 6. Programstruktur

    bibliotekside/
    ├── static/
    │   └── style.css
    ├── templates/
    │   ├── admin/
    │   │   └── borrowings.html
    │   ├── user/
    │   │   ├── browse.html
    │   │   └── my_loans.html
    │   └── login.html
    ├── venv/
    ├── .env
    ├── .gitignore
    ├── app.py
    ├── app-env.py
    ├── db_conn.py
    ├── requirements.txt
    └── run.py
Databasestrøm:

    Nettleser (HTTP request) → Waitress (sender til Flask) → Flask app.py (kaller get_connection()) → db_conn.py (SQL spørring) → MariaDB (returnerer data) → Flask app.py (sender data til template) → Jinja2 (setter inn data i HTML) → Nettleser

------------------------------------------------------------------------

## 7. Kodeforklaring



| Metode | Rute | Hva den gjør |
|--------|-------|-------------|
| GET/POST | `/login` | Innlogging, redirect basert på rolle |
| GET | `/logout` | Tøm session, redirect til login |
| GET | `/admin/borrowings` | Se alle låneforespørsler |
| POST | `/admin/borrowings/approve/<id>` | Godkjenn forespørsel, sett forfallsdato |
| POST | `/admin/borrowings/reject/<id>` | Avslå forespørsel |
| POST | `/admin/borrowings/return/<id>` | Marker som returnert |
| GET | `/browse` | Katalog over bøker |
| POST | `/browse/request/<book_id>` | Send låneforespørsel |
| GET | `/my-loans` | Se egne lån og historikk |
| POST | `/my-loans/return/<id>` | Returner bok selv |

Login-ruten sjekker at brukeren finnes i databasen og at bcrypt.check_password_hash stemmer. Ved godkjent innlogging lagres user_id, name og role i session, og brukeren redirectes til riktig side.

Alle admin-ruter starter med:
if session.get('role') != 'admin':
    return redirect(url_for('login'))

Alle bruker-ruter starter med:
if 'user_id' not in session:
    return redirect(url_for('login'))

"SELECT id FROM borrowings 
WHERE book_id = (SELECT book_id FROM borrowings WHERE id = %s) 
AND status = 'active'" Sørger for at systemet ikke tillater at to personer har den samme boken.






------------------------------------------------------------------------

## 8. Sikkerhet og pålitelighet

-   .env og Miljøvariabler: All sensitiv informasjon lagres i en .env-fil som ikke lastes opp til GitHub (.gitignore). Flask leser verdiene via python-dotenv og os.getenv().

-   Parameteriserte spørringer: Alle SQL-spøøringer bruker %s-parametere i stedet for string-formatering. Dette forhindrer SQL-injeksjon.
  
-   Bcrypt passord-hashing: Passord lagres aldri i tekst. Ved registrering hashes passordet med bcrypt.generate_password_hash().
  
-   Sessions: Flask sessions brukes til å holde brukeren innlogget. Ved innlogging lagres user_id, name og role i session. Ved utlogging tømmes session med session.clear().
  
-   Feilhåndtering: En del av koden som skriver data er pakket i try/except. Ved feil kalles conn.rollback() for å angre transaksjonen og brukeren får melding om at noe gikk galt.

------------------------------------------------------------------------

## 9. Feilsøking og testing

-   Typiske feil\
-   Hvordan du løste dem\
  **Testmetoder**
   - Manuell testing i nettleser ved å teste alle ruter med ulike brukerroller

------------------------------------------------------------------------

## 10. Konklusjon og refleksjon

-   Hva lærte du?\
-   Hva fungerte bra?\
-   Hva ville du gjort annerledes?\
-   Hva var utfordrende?

------------------------------------------------------------------------

## 11. Kildeliste

-   w3schools\
-   flask.palletsprojects.com
