from itertools import count
import re
from flask import Flask, flash, render_template,request, redirect, url_for , session, jsonify
from flask import send_file, send_from_directory
import io
import os
import sqlite3
import base64
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(20)

conn=sqlite3.connect('online_voting.db')
conn.execute("PRAGMA journal_mode=WAL;")
conn.close()

# ----------------------------
# Database connection
# ----------------------------

def get_db_connection():
    conn = sqlite3.connect('online_voting.db',timeout=10,check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ----------------------------
# Home page (optional)
# ----------------------------

@app.route('/')
def home():
    return render_template('Home.html')

#========register info==========

@app.route('/register_info')
def register_info():
    return render_template("register_info.html")

#========restrictions==========

@app.route('/restrictions')
def restrictions():
    return render_template("restrictions.html")

# =============support============
@app.route('/support',methods=["GET" , "POST"] )
def support():
    if request.method== "POST":
     
     name=request.form["s_name"]
     email=request.form["email"]
     message=request.form["message"]

     conn=get_db_connection()
     try:
      cur=conn.cursor()

      cur.execute("""
                INSERT INTO support (name,email,message)VALUES(?,?,?)
                 """, (name,email,message))
      conn.commit()
     finally:
      conn.close()
     return "submitted successfuly, <a href='/help'>go back</a>"
    return render_template('help.html')

# ===============show=================
@app.route('/show_elections')
def show_elections():
    return render_template("show_elections.html")


# ==========registration user page=================

@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        gender = request.form["gender"]
        dob = request.form["dob"]
        adhar_number = request.form["adhar_number"]
        voter_id = request.form["voter_id"]
        password = request.form["password"]
        hashed_password=generate_password_hash(password)


        conn = get_db_connection()
        try:
          cursor = conn.cursor()

          cursor.execute("""
            INSERT INTO registration_information
            (fullname,email,mobile,gender,dob,password,adhar_number,voter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fullname, email, mobile, gender, dob, hashed_password, adhar_number, voter_id))

          conn.commit()
        finally:
         conn.close()

    
   
         return redirect("/user_login")

    return render_template("registration.html")

# ==========login user page=================

@app.route('/user_login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        try:
          user = conn.execute(
            "SELECT * FROM registration_information WHERE mobile=?",
            (mobile,)
            ).fetchone()
        finally:
          conn.close()

        if user and check_password_hash(user[8],password):
            session['voter_id'] = user['voter_id']
            print("debug voter id saved in session:", session['voter_id'])
            return redirect('/user_home')
        else:
            return "Invalid mobile or password. Please try again. <a href='/user_login'>Go Back</a>"

    return render_template('user_login.html')

# ==========user home page=================

@app.route('/user_home')
def user_home():
    conn=sqlite3.connect('online_voting.db')
    try:
      cur=conn.cursor()

      cur.execute("SELECT election_name FROM election_info ORDER BY eid DESC")
      elections=cur.fetchall()
    finally:
     conn.close()

    return render_template('user_home.html', elections=elections)


# ===============logout ==================

@app.route('/logout_user')
def logout_user():
    session.clear()
    return redirect(url_for('login'))

# ---------------vote---------------
   
@app.route("/vote_page", methods=["GET"] )
def vote_page(): 
    print("debug: vote_page accessed",session )  # DEBUG
    con = get_db_connection()
    try:
     cur = con.cursor()

     cur.execute("SELECT * FROM candidate_information")
     rows = cur.fetchall()
    finally: 
     con.close()

    candidates = []
    for row in rows:
        logo = ""
        if row["party_logo"]:
            logo = base64.b64encode(row["party_logo"]).decode("utf-8")

        candidates.append({
            "id": row["id"],
            "candidate_name": row["candidate_name"],
            "party_name": row["party_name"],
            "party_logo": logo
        })

    message = "इथे काळजीपूर्वक उमेदवार पाहून त्याच्या समोरील बटण दाबा"
    return render_template("vote_page.html", candidates=candidates, message=message)

# ---------------vote submission---------------

@app.route("/vote_candidate", methods=["POST"])
def vote_candidate():
    candidate_id = request.form["candidate_id"]
    voter_id = session["voter_id"] # optional, static if no login

    conn = get_db_connection()
    cursor= conn.cursor()
    
    cursor.execute("SELECT * FROM votes WHERE voter_id=?", (voter_id,))
    existing_vote = cursor.fetchone()
    if existing_vote:
       conn.close()
       return "You have already voted. <a href='/user_home'>Go Back</a>"
    
    cursor.execute(
     "SELECT candidate_name FROM candidate_information WHERE id=?",
     (candidate_id,))
 
    candidate_row = cursor.fetchone()
    candidate_name = candidate_row[0]



     # insert vote
    cursor.execute("INSERT INTO votes (candidate_id, candidate_name, voter_id) VALUES (?, ?,?)", (candidate_id,candidate_name, voter_id))
    conn.commit()
    conn.close()

    
    flash("Vote successful!", "success")
    return redirect("/user_home")

# ==========admin home page=================

@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html', candidate_count=get_candidate_count(), voter_count=get_voter_count())

# -------------candidate count ------------------

def get_candidate_count():
    conn = get_db_connection()
    try:
     cursor = conn.cursor()
     cursor.execute("SELECT COUNT(*) FROM candidate_information")
     count = cursor.fetchone()[0]
    finally:
     conn.close()
     return count

# ---------------voters count ------------------

def get_voter_count():
    conn = get_db_connection()
    try:
     cursor = conn.cursor()
     cursor.execute("SELECT COUNT(*) FROM registration_information")
     count = cursor.fetchone()[0]
    finally:
     conn.close()
     return count

# ==========about page=================

@app.route('/about')
def about():
    return render_template('about.html')

#============help=====================

@app.route('/help')
def help():
    return render_template('help.html')

#=============help request===============

@app.route('/help_request')
def help_request():
    conn = get_db_connection()
    try:
     cursor = conn.cursor()

     cursor.execute("SELECT * FROM support ")
     rows = cursor.fetchall()  # sagle records fetch zala
    finally:
     conn.close()

     requests=[]

     for row in rows:
         requests.append({
             "sid": row["sid"],
             "name": row["name"],
             "email": row["email"],
             "message": row["message"]
         })
     return render_template('help_request.html', requests=requests)

# ==========instruction user page=================

@app.route('/instruction_user')
def instruction_user():
    return render_template('instruction_user.html')

# =============election info================

@app.route('/add_election', methods=['GET', 'POST'])
def add_election():
    if request.method == 'POST':
        election_name = request.form['election_name']
        election_date = request.form['election_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']


        conn = get_db_connection()
        try:
         cursor = conn.cursor()

         cursor.execute("""
             INSERT INTO election_info
             (election_name, election_date, start_time, end_time)
             VALUES (?, ?, ?, ?)
          """, (election_name, election_date, start_time, end_time))

         conn.commit()
        finally:
         conn.close()

         return render_template("add_election.html", message="election info added successfully")
    return render_template("add_election.html")

# ================= ADMIN LOGIN =================

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        try:
         user = conn.execute(
             "SELECT * FROM admin_information WHERE username=? AND password=?",
             (username, password)
         ).fetchone()
        finally:
         conn.close()

         if user:
             return redirect('/admin_home')
         else:
             return "Invalid username or password. <a href='/admin_login'>Go Back</a>"

    return render_template('admin_login.html')
    
# ===============logout ==================

@app.route('/logout_admin')
def logout_admin():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/reset_data')
def reset_data():
    con = get_db_connection()
    try:
     cur = con.cursor()

     cur.execute("DELETE FROM candidate_information")
     cur.execute("DELETE FROM votes")
     cur.execute("DELETE FROM election_info")
     cur.execute("DELETE FROM support")

     con.commit()
    finally:
     con.close()

     return jsonify({"status": "reset"})

# ================Remove Users=================

@app.route('/remove_all_users')
def remove_all_users():
    conn = get_db_connection()
    try:
     cur = conn.cursor()

     # registration_information table clear
     cur.execute("DELETE FROM registration_information")

     conn.commit()
    finally:
     conn.close()

     return jsonify({
         "status": "success",
         "message": "All users removed successfully"
     })

# ==============add_candidate=================

@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        candidate_name = request.form['candidate_name']
        party_name = request.form['party_name']
        party_logo = request.files['party_logo'].read()

        election_date = request.form['election_date']

        conn = get_db_connection()
        try:
         cursor = conn.cursor()

         cursor.execute("""
             INSERT INTO candidate_information
             (candidate_name, party_name, party_logo, election_date)
             VALUES (?, ?, ?, ?)
         """, (candidate_name, party_name, party_logo, election_date))

         conn.commit()
        finally:
         conn.close()

         return render_template('add_candidate.html', message="Candidate added successfully!")
    
    return render_template('add_candidate.html')

# ==============view_candidates=================

@app.route("/view_candidates")
def view_candidates():

    con = get_db_connection()
    try:
     cur = con.cursor()

     cur.execute("SELECT * FROM candidate_information")
     rows = cur.fetchall()

     print("ROWS FOUND =", len(rows))   # DEBUG
    finally:
     con.close()

     candidates = []

     for row in rows:
         logo = ""
         if row["party_logo"]:
             logo = base64.b64encode(row["party_logo"]).decode("utf-8")

         candidates.append({
             "id": row["id"],
             "candidate_name": row["candidate_name"],
             "party_name": row["party_name"],
             "election_date": row["election_date"],
             "party_logo": logo
         })

    return render_template("view_candidates.html", candidates=candidates)

# ===============results=================

@app.route('/result')
def view_result():
    conn = get_db_connection()
    try:
     cur = conn.cursor()

     query = """
         SELECT 
             candidate_id,
             candidate_name,
             COUNT(candidate_id) AS total_votes
         FROM votes
         GROUP BY candidate_id, candidate_name
         ORDER BY total_votes DESC
     """

     cur.execute(query)
     results = cur.fetchall()
    finally:
     conn.close()

     return render_template('result.html', results=results)

# ===========show election=============
@app.route('/show_election')
def show_election():
    conn = get_db_connection()
    try:
     cur = conn.cursor()

     cur.execute("SELECT election_name FROM election_info ORDER BY eid DESC")
     elections=cur.fetchall()
    finally:
     conn.close()

     return render_template('show_election.html', elections=elections)
    
# ================END==================

if __name__ == "__main__":
    app.run(debug=False)
