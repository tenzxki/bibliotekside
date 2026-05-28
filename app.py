from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt 
from db_conn import get_connection
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"
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

#Lage admin borrowings route her
#@app.route('/admin/borrowings')
#def admin_borrowings():
    



@app.route('/browse')
def browse():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

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

#Lage reject borrowing routen her
#@app.route('/admin/borrowings/reject/<int:id>', methods=['POST'])
#def reject_borrowing(id):
    

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

if __name__ == '__main__':
    app.run(debug=True)

    



