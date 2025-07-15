from flask_wtf import FlaskForm
from wtforms import StringField,TelField
from wtforms.validators import input_required


class Search_form(FlaskForm):
    role = StringField(label='Role', validators=[input_required()])
    person_id = StringField(label='Person_id', validators=[input_required()])
    entry_exit = StringField(label='Entry/Exit',validators=[input_required()])

class Visitor_entry(FlaskForm):
    name = StringField(label='Name',validators=[input_required()])
    ph_no = TelField(label='Ph_n0',validators=[input_required()])
    email = StringField(label='Email',validators=[input_required()])
    faculty_name = StringField(label='Faculty',validators=[input_required()])
    faculty_dept = StringField(label='Dept',validators=[input_required()])
    reason = StringField(label='reason',validators=[input_required()])

class Visitor_exit(FlaskForm):
    name = StringField(label='Name', validators=[input_required()])
    ph_no = TelField(label='Ph_n0', validators=[input_required()])

