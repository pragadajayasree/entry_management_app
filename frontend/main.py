from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, desc
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from forms import Search_form, Visitor_entry, Visitor_exit
from twilio.rest import Client
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret')

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/data.db')

db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Students(UserMixin, db.Model):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    reg_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dept: Mapped[str] = mapped_column(String, nullable=False)
    ph_no: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

class Faculty(UserMixin, db.Model):
    __tablename__ = "faculty"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    reg_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dept: Mapped[str] = mapped_column(String, nullable=False)
    ph_no: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

class Entry_log(UserMixin, db.Model):
    __tablename__ = "entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    reg_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dept: Mapped[str] = mapped_column(String, nullable=False)
    ph_no: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    entry_time: Mapped[str] = mapped_column(String, nullable=True)
    exit_time: Mapped[str] = mapped_column(String, nullable=True)

class Visitors_log(UserMixin, db.Model):
    __tablename__ = "visitors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    ph_no: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    faculty_name: Mapped[str] = mapped_column(String, nullable=False)
    faculty_dept: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    entry_time: Mapped[str] = mapped_column(String, nullable=True)
    exit_time: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/safety')
def safety():
    return render_template('safety.html')

@app.route('/entry_log', methods=['GET', 'POST'])
def entry_log():
    form = Search_form()
    if request.method == 'POST' and form.validate_on_submit():
        role = form.role.data.lower()
        person_id = form.person_id.data.upper()
        current_date = date.today().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%I:%M %p")

        user = None
        if role == 'student':
            user = db.session.execute(db.select(Students).where(Students.reg_id == person_id)).scalar()
        elif role == 'faculty':
            user = db.session.execute(db.select(Faculty).where(Faculty.reg_id == person_id)).scalar()

        if not user:
            flash('User does not exist!', 'danger')
            return redirect(url_for('entry_log'))

        entry = db.session.execute(
            db.select(Entry_log).where(Entry_log.reg_id == person_id, Entry_log.date == current_date)
        ).scalar()

        if not entry or (entry.entry_time and entry.exit_time):
            new_entry = Entry_log(
                role=role.upper(),
                reg_id=user.reg_id.upper(),
                name=user.name.upper(),
                dept=user.dept.upper(),
                ph_no=user.ph_no,
                email=user.email,
                date=current_date,
                entry_time=None,
                exit_time=None,
            )
            db.session.add(new_entry)
            if form.entry_exit.data.lower() == 'exit':
                new_entry.exit_time = current_time
            else:
                new_entry.entry_time = current_time
        else:
            if form.entry_exit.data.lower() == 'exit':
                entry.exit_time = current_time
            else:
                entry.entry_time = current_time

        db.session.commit()
        flash('Entry recorded successfully!', 'success')
        return redirect(url_for('entry_log'))

    return render_template('entry_log.html', form=form)

@app.route('/visitors')
def visitors():
    if 'security_message' in session:
        flash(session['security_message']['message'], session['security_message']['category'])
        session.pop('security_message')
    return render_template('visitors.html')

def send_sms_to_faculty(visitor_id, faculty_phone, visitor_name, visitor_reason):
    account_sid = os.environ.get('ACCOUNT_SID')
    auth_token = os.environ.get('AUTH_TOKEN')
    from_number = os.environ.get('PH_NO')

    if not all([account_sid, auth_token, from_number]):
        print("Missing Twilio credentials.")
        return

    client = Client(account_sid, auth_token)
    public_url = request.host_url.rstrip('/')

    accept_url = f"{public_url}/update_status/{visitor_id}/ACCEPTED"
    reject_url = f"{public_url}/update_status/{visitor_id}/REJECTED"

    message = f"""
    Visitor {visitor_name} wants to meet you.
    reason: {visitor_reason}
    Accept: {accept_url}
    Reject: {reject_url}
    """

    client.messages.create(
        body=message,
        from_=from_number,
        to=f'+91{faculty_phone}'
    )

@app.route('/visitors_entry', methods=['GET', 'POST'])
def visitors_entry():
    form = Visitor_entry()
    if request.method == 'POST' and form.validate_on_submit():
        name = form.name.data.upper()
        ph_no = form.ph_no.data
        email = form.email.data
        faculty_name = form.faculty_name.data.upper()
        faculty_dept = form.faculty_dept.data.upper()
        reason = form.reason.data
        current_date = date.today().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%I:%M %p")

        result = db.session.execute(
            db.select(Faculty).where(Faculty.name == faculty_name)
        ).scalar()

        if result is None:
            flash("❌ No such faculty exists. Please check the name and try again.", "danger")
            return redirect(url_for('visitors_entry'))

        new_user = Visitors_log(
            name=name,
            ph_no=ph_no,
            email=email,
            faculty_name=faculty_name,
            faculty_dept=faculty_dept,
            reason=reason,
            date=current_date,
            entry_time=current_time,
            exit_time=None,
            status='pending'
        )

        db.session.add(new_user)
        db.session.commit()

        faculty_ph_no = result.ph_no
        send_sms_to_faculty(visitor_id=new_user.id, faculty_phone=faculty_ph_no, visitor_name=name, visitor_reason=reason)

        return redirect(url_for('visitors'))

    return render_template('visitors_entry.html', form=form)

@app.route('/update_status/<int:visitor_id>/<response>', methods=['GET'])
def faculty_response(visitor_id, response):
    if response not in ["ACCEPTED", "REJECTED"]:
        return "Invalid response.", 404

    visitor = Visitors_log.query.get_or_404(visitor_id)
    visitor.status = response
    db.session.commit()
    session['security_message'] = {
        'message': f"{visitor.faculty_name} has {response.upper()} the request from {visitor.name}.",
        'category': "success" if response == "ACCEPTED" else "danger"
    }

    message = f"You have {response} the visitor request."
    return render_template("faculty_response.html", message=message)

@app.route('/visitors_exit', methods=['GET', 'POST'])
def visitors_exit():
    form = Visitor_exit()
    if request.method == 'POST' and form.validate_on_submit():
        name = form.name.data.upper()
        ph_no = form.ph_no.data
        current_date = date.today().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%I:%M %p")
        user = db.session.execute(
            db.select(Visitors_log).where(
                Visitors_log.name == name,
                Visitors_log.ph_no == ph_no,
                Visitors_log.date == current_date
            )
        ).scalar()
        user.exit_time = current_time
        db.session.commit()
        return redirect(url_for('visitors'))
    return render_template('visitors_exit.html', form=form)

@app.route('/reports')
def reports():
    current_date = date.today().strftime("%Y-%m-%d")
    students = db.session.execute(
        db.select(Entry_log).where(
            Entry_log.role == 'STUDENT',
            Entry_log.date == current_date
        ).order_by(desc(Entry_log.entry_time))
    ).scalars()
    faculty = db.session.execute(
        db.select(Entry_log).where(
            Entry_log.role == 'FACULTY',
            Entry_log.date == current_date
        ).order_by(desc(Entry_log.entry_time))
    ).scalars()
    visitors = db.session.execute(
        db.select(Visitors_log).where(
            Visitors_log.date == current_date
        ).order_by(desc(Visitors_log.entry_time))
    ).scalars()
    return render_template('reports.html', students=students, faculty=faculty, visitors=visitors)

@app.route('/search', methods=['POST'])
def search():
    result = request.form['query'].upper()
    list = db.session.execute(
        db.select(Entry_log).where(
            Entry_log.name == result
        ).order_by(desc(Entry_log.entry_time))
    ).scalars()
    visitor = db.session.execute(
        db.select(Visitors_log).where(
            Visitors_log.name == result
        ).order_by(desc(Visitors_log.entry_time))
    ).scalars()
    return render_template('search.html', list=list, visitors=visitor)
