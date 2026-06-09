from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt 
from db_conn import get_connection
from dotenv import load_dotenv
from waitress import serve
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_borrowings'))
    else:
        return redirect(url_for('browse'))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        navn = request.form['name']
        email = request.form['email']
        passord = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')",
                        (navn, email, passord))
            conn.commit()
            flash("Bruker registrert!", "success")
            cursor.close()
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            conn.rollback()
            flash("Email er allerede i bruk!", "error")
            print(f"Error: {e}")
            cursor.close()
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        passord = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        bruker = cursor.fetchone()
        cursor.close()
        conn.close()

        if bruker and bcrypt.check_password_hash(bruker['password'], passord):
            session['user_id'] = bruker['id']
            session['name'] = bruker['name'] 
            session['role'] = bruker['role']
            session['email'] = bruker['email']

            if bruker['role'] == 'admin':
                return redirect(url_for("admin_borrowings"))
            else:
                return redirect(url_for("browse"))
        else:
            flash("Feil email eller passord", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("Du er nå logget ut", "info")
    return redirect(url_for('login'))


@app.route('/admin/borrowings')
def admin_borrowings():
    if session.get('role') != 'admin':
        return redirect (url_for('login'))
    
    status_filter = request.args.get('status', 'all')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if status_filter == 'all':
        cursor.execute("""
            SELECT borrowings.*, books.title, users.name
            FROM borrowings
            JOIN books ON borrowings.book_id = books.id
            JOIN users ON borrowings.user_id = users.id
            ORDER BY borrowings.created_at DESC
       """)
    else:
        cursor.execute("""
            SELECT borrowings.*, books.title, users.name
            FROM borrowings
            JOIN books ON borrowings.book_id = books.id
            JOIN users ON borrowings.user_id = users.id
            WHERE borrowings.status = %s
            ORDER BY borrowings.created_at DESC
        """, (status_filter,))

    borrowings = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/borrowings.html', borrowings=borrowings, status_filter = status_filter)


@app.route('/browse', methods=['GET', 'POST'])
def browse():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    #Fikk litt hjelp av gemini til å starte.

    if request.method == 'POST' and session.get('role') == 'admin':
        action = request.form.get('action')
    
        if action == 'create_book':
            title = request.form['title']
            author = request.form['author']
            genre = request.form['genre']
            try:
                cursor.execute("INSERT INTO books (title, author, genre) VALUES (%s, %s, %s)", (title, author, genre))
                conn.commit()
                flash("Boken ble lagt til i biblioteket!")
            except Exception as e:
                conn.rollback()
                flash("Kunne ikke legge til boken.")
                print(f"Feil: {e}")
    
        elif action == 'update_book':
            book_id = request.form['book_id']
            title = request.form['title']
            author = request.form['author']
            genre = request.form['genre']
            try:
                cursor.execute("""
                    UPDATE books 
                    SET title = %s, author = %s, genre = %s 
                    WHERE id = %s
                """, (title, author, genre, book_id))
                conn.commit()
                flash("Boken ble oppdatert!")
            except Exception as e:
                conn.rollback()
                flash("Kunne ikke oppdatere boken.")
                print(f"Feil: {e}")

        return redirect(url_for('browse'))

    cursor.execute("SELECT * FROM books ORDER BY title")
    bøker = cursor.fetchall()

    cursor.execute("""
    SELECT book_id FROM borrowings
    WHERE status IN ('pending', 'active')
    """)
    opptatte = [row['book_id'] for row in cursor.fetchall()] #Hjelp av Claude

    cursor.close()
    conn.close()

    return render_template('user/browse.html', bøker=bøker, opptatte=opptatte)

@app.route('/my-loans')
def my_loans():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

#Litt hjelp av claude
    cursor.execute("""
        SELECT br.*, b.title
        FROM borrowings br
        JOIN books b ON br.book_id = b.id
        WHERE br.user_id = %s AND br.status IN ('pending', 'active') 
        ORDER BY br.created_at DESC
    """, (session['user_id'],))
    aktive = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user/my_loans.html', aktive=aktive)



@app.route('/browse/request/<int:book_id>', methods=['POST'])
def request_loan(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id FROM borrowings
            WHERE book_id = %s AND status IN ('pending', 'active')
        """, (book_id,))

        if cursor.fetchone():
            flash("Denne boken er ikke tilgjengelig")
        else:
            cursor.execute("""
                INSERT INTO borrowings (book_id, user_id)
                VALUES (%s, %s)
            """, (book_id, session['user_id']))
            conn.commit()
            flash("Låneforespørsel sendt!")
    except Exception as e:
        conn.rollback()
        flash("Noe gikk galt")
        print(f"Feil: {e}")

    cursor.close()
    conn.close()
    return redirect(url_for('browse'))


@app.route('/admin/borrowings/approve/<int:id>', methods=['POST'])
def approve_borrowing(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    due_date = request.form['due_date']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    #Spørringen under er fra Claude
    try:
        cursor.execute("""  
            UPDATE borrowings
            SET status = 'active', borrowed_at = CURDATE(), due_date = %s
            WHERE id = %s
        """, (due_date, id))
        conn.commit()
        flash("Forespørsel godkjent!")
    except Exception as e:
        conn.rollback()
        flash("Noe gikk galt")
        print(f"Feil: {e}")

    cursor.close()
    conn.close()
    return redirect(url_for('admin_borrowings'))


@app.route('/admin/borrowings/reject/<int:id>', methods=['POST'])
def reject_borrowing(id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            DELETE FROM borrowings 
            WHERE id = %s AND status = 'pending'
        """, (id,))
        conn.commit()
        flash("Låneforespørsel ble avvist og fjernet.")
    except Exception as e:
        conn.rollback()
        flash("Noe gikk galt under avvisning.")
        print(f"Feil: {e}")

    cursor.close()
    conn.close()
    return redirect(url_for('admin_borrowings'))

@app.route('/admin/borrowings/return/<int:id>', methods = ['POST'])
def return_borrowing(id):
    if session.get('role') != 'admin':
        return redirect(url_for(login))
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE borrowings
        SET status = 'returned', returned_at = CURDATE()
        WHERE id = %s AND status = 'active'
    """,(id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_borrowings'))


@app.route('/admin/books/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        flash("Boken ble slettet manuelt fra systemet!")
    except Exception as e:
        conn.rollback()
        flash("Kan ikke slette boken! Den er knyttet til et eksisterende eller historisk utlån.")
        print(f"Feil ved sletting: {e}")
        
    cursor.close()
    conn.close()
    return redirect(url_for('browse'))



@app.route('/faq', methods=['GET', 'POST'])
def faq():
    LoggedIn = 'user_id' in session

    if request.method == 'POST':

        if 'sporsmal' in request.form:
            sporsmal = request.form['sporsmal']

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            try:
                cursor.execute(
                    "INSERT INTO faq (sporsmal, user_id) VALUES (%s, %s)",
                    (sporsmal, session['user_id'])
                )
                conn.commit()
                flash("Spørsmål sendt!")
            except Exception as e:
                conn.rollback()
                flash("Noe gikk galt")
                print(f"Feil: {e}")

            cursor.close()
            conn.close()
            return redirect(url_for('faq'))

        elif 'email' in request.form:
            email = request.form['email']

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            try:
                cursor.execute("""
                    UPDATE users
                    SET
                        name = 'Slettet bruker',
                        email = CONCAT('deleted_', id, '@library.com')
                    WHERE email = %s
                """, (email,))
                conn.commit()
                flash("Bruker anonymisert!")
            except Exception as e:
                conn.rollback()
                flash("Noe gikk galt")
                print(f"Feil: {e}")

            cursor.close()
            conn.close()
            return redirect(url_for('faq'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT f.*, u.name, u.email
        FROM faq f
        JOIN users u ON f.user_id = u.id
        ORDER BY f.opprettet DESC
    """)
    sporsmal = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('user/faq.html', sporsmal=sporsmal, LoggedIn=LoggedIn)


#if __name__ == '__main__':
#   app.run(debug=True)


if __name__ == '__main__':
 serve(app, host='0.0.0.0', port=8080)

    



