from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "change_later"


#CONFIG SQLALCH
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


#user DB model
class User(db.Model):
    #class variables
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)


    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash, password)

#Poll model
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(250), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='polls')
    votes = db.relationship('Vote', backref='poll', lazy=True)

#Vote count model
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    choice = db.Column(db.String(1), nullable=False) 
    voter = db.relationship('User', backref='votes')







#routes
@app.route("/")
def home():
    if "username"in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")



#login
@app.route("/login", methods=["POST"])
def login():
    username = request.form['username']
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password.")
        return redirect(url_for('home'))



#register
@app.route("/register", methods=["POST"])
def register():
    username = request.form['username']
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user:
        flash("Username taken, pick another one.")
        return redirect(url_for('home'))
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    session['username'] = username
    return redirect(url_for('dashboard'))





#dashboard
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        user = User.query.filter_by(username=session['username']).first()
        my_polls = Poll.query.filter_by(creator_id=user.id).all()
        all_polls = Poll.query.all()
        return render_template("dashboard.html", username=session['username'], my_polls=my_polls,all_polls=all_polls)
    return redirect(url_for('home'))



#Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for('home'))


#Create poll
@app.route("/create_poll", methods=["POST"])
def create_poll():
    if "username" not in session:
        return redirect(url_for('home'))

    question = request.form["question"]
    option_a = request.form["option_a"]
    option_b = request.form["option_b"]

    
    user = User.query.filter_by(username=session["username"]).first()

    new_poll = Poll(
        question=question,
        option_a=option_a,
        option_b=option_b,
        creator_id=user.id
    )

    db.session.add(new_poll)
    db.session.commit()

    flash("Poll created successfully!")
    return redirect(url_for('dashboard'))

#voting
@app.route("/vote/<int:poll_id>", methods=["POST"])
def vote(poll_id):
    if "username" not in session:
        return redirect(url_for("home"))

    user = User.query.filter_by(username=session["username"]).first()
    poll = Poll.query.get_or_404(poll_id)

    #do not allow the account to vote twice.
    existing_vote = Vote.query.filter_by(user_id=user.id, poll_id=poll_id).first()
    if existing_vote:
        flash("You have already voted on this poll.")
        return redirect(url_for("dashboard"))

    choice = request.form.get("choice")
    if choice not in ["A", "B"]:
        flash("Invalid vote.")
        return redirect(url_for("dashboard"))

    new_vote = Vote(user_id=user.id, poll_id=poll_id, choice=choice)
    db.session.add(new_vote)
    db.session.commit()

    flash("Vote submitted!")
    return redirect(url_for("dashboard"))





if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)