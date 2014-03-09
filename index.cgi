#!/usr/bin/python

import sys
import os
import sqlite3
import cgi
import smtplib
from email.mime.text import MIMEText
import datetime

# Create database pending.db read/writable by www-data
# $ sqlite3 pending.dp
# sqlite> CREATE TABLE member(real_name, username, address, membership_type, guild_member, phone_number, email_address, student_no, date_of_birth, gender, signed_up, paid);
# Get rid of database by DROP TABLE or deleting the file


target_email = "exec@ucc.asn.au" # Who will be notified
secret_answers = ["Tux","tux","TUX","Penguin","penguin","PENGUIN"]
def print_form(name):
	""" Print the form """
	f = open(name,"r")
	for line in f.readlines():
		print(line)
	f.close()

if __name__ == "__main__":
	""" Do the shit """
	con = sqlite3.connect("pending.db")
	c = con.cursor()

	# Values we expect
	values = {
		"real_name" : "",
		"username" : "",
		"address" : "",
		"membership_type" : "",
		"guild_member" : False,
		"phone_number" : "",
		"email_address" : "",
		"student_no" : "",
		"date_of_birth" : "",
		"gender" : "",
	}

	form = cgi.FieldStorage()
	# No values? Print the form
	if len(form.keys()) <= 0:
		print("Content-type: text/html\n")
		print_form("form.html")
		sys.exit(0)

	# Check we have all the values
	for k in values.keys():
		if k not in form:
			print("Content-type: text/html\n")
			print("<p><b>Missing value for %s</b></p>" %k)
			print_form("form.html")
			sys.exit(0)	
		values[k] = form[k].value

	# Sanity checks!

	# Check secret question
	if form["secret"].value not in secret_answers: 
		print("content-type: text/html\n")
		print("<p><b>Incorrect or missing secret answer</b></p>")
		print_form("form.html")
		sys.exit(0)

	# Check user aggress
	if "agree" not in form or form["agree"].value not in ["yes"]:
		print("content-type: text/html\n")
		print("<p><b>You must agree to abide by the UCC's constitution, rulings of the UCC Committee and network usage guildlines</b></p>")
		print_form("form.html")
		sys.exit(0)
	
	# Check user isn't already in database
	c.execute("SELECT * FROM member WHERE username=?", (values["username"],))
	if len(c.fetchall()) > 0:
		print("Status:400\n")
		print("User already registered")
		print("If you registered *last* year but not this year, poke committee@ucc.asn.au to reset the database.")
		sys.exit(0)

	# Check email isn't already in database
	c.execute("SELECT * FROM member WHERE email_address=?", (values["email_address"],))
	if len(c.fetchall()) > 0:
		print("Status:400\n")
		print("Email already registered.\n")
		print("If you registered *last* year but not this year, poke committee@ucc.asn.au to reset the database.")
		sys.exit(0)

	# Sanity checks complete; set other values
	values.update({"signed_up" : datetime.datetime.now()})
	values.update({"paid" : "No"})

	# Produce emails
	generic = "The following information was registered for UCC Membership:\n\n"
	hidden_fields = ["phone_number", "date_of_birth", "student_no", "address"] # Don't email these fields
	for k in values.keys():
		if k not in hidden_fields:
			generic += "%s: %s\n" % (k, values[k])
		else:
			generic += "%s: <hidden>\n" % k

	userMsg = "Dear %s\n\n" % values["real_name"].split(" ")[0]
	userMsg += generic + "\n\n"
	userMsg += "Payment details:\n"
	userMsg += "Bank: Westpac Bank\nAccount: The University Computer Club\nAccount Number: 285739\nBSB: 036054\nDescription: %s\n\nOr via dispense." % values["username"]
	userMsg += "If this is incorrect, please contact %s\n\n" % target_email 
	userMsg += "Warm regards,\n%s" % sys.argv[0]

	execMsg = "Dear Wizengamot,\n\n"
	execMsg += generic + "\n\n"


	execMsg += "On motsugo run the next line to see all the fields:\n"
	execMsg += "echo \"SELECT * FROM member WHERE email_address = \'%s\';\" | sqlite3 /services/gms/register/pending.db\n\n" % values["email_address"]
	execMsg += "Once you are satisfied payment has been made, please add these details to MemberDB at:\n https://secure.ucc.asn.au/members\n"
	execMsg += "If there are any problems contact wheel@ucc.asn.au\n\n"


	execMsg += "Warm regards,\n%s" % sys.argv[0]
	# Send emails

	userMsg = MIMEText(userMsg)
	execMsg = MIMEText(execMsg)
	emails = [values["email_address"], target_email] 
	for i,msg in enumerate([userMsg, execMsg]):
		msg["Subject"] = "UCC Member Registration"
		msg["From"] = "exec@ucc.asn.au"
		msg["To"] = emails[i]
		s = smtplib.SMTP("localhost")
		s.sendmail(msg["From"], [msg["To"]], msg.as_string())
		s.quit()

	# Tell them what happened.
	print("Content-type: text/plain\n")
	print("You should receive the following email shortly:\n\n")
	print(userMsg)	

	# Do the thing
	c.execute("INSERT INTO member("+",".join(values.keys())+") VALUES("+",".join(["?" for _ in xrange(len(values.keys()))])+")", [values[k] for k in values.keys()])
	con.commit()
	con.close()

	sys.exit(0)
	
	


