from flask import Flask, render_template, request, redirect, make_response
from mongita import MongitaClientDisk
from bson import ObjectId
from passwords import hash_pwd # (password) -> hashed_password, salt
from passwords import check_pwd # (password, saved_hash_password, salt)
from datetime import date

app = Flask(__name__)

# Writing the data to a Mongita DB file
# Create Mongita Client connection
client = MongitaClientDisk()

# create a quotes DB
quotes_db = client.quotes_db
session_db = client.session_db
user_db = client.user_db
comments_db = client.comments_db

import uuid

#Generating uuuid session key
session_key = uuid.uuid4()

##################
# Login/Logout
##################

@app.route("/logout", methods=["GET"])
def get_logout():
        #get session_id
        session_id = request.cookies.get("session_id", None)
        #if session id exists
        if session_id:
                #open the session db collection
                session_collection = session_db.session_collection
                #deleting the session information from the database
                session_collection.delete_one({"session_id": session_id})
        response = redirect("/login")
        response.delete_cookie("session_id")
        user_collection = user_db.user_collection
        print(user_db.user_collection.find())
        return response

@app.route("/login", methods=["POST"])
def post_login():
        #get the user from the form input field
        user = request.form.get("user", "")
        #get password from the form input field
        password = request.form.get("password", "")
        #open user collection
        user_collection = user_db.user_collection
        #set user data
        user_data = list(user_collection.find({"user": user}))
        if len(user_data) != 1:
                response = redirect("/login")
                response.delete_cookie(session_id)
                return response
        #get hashed password from db
        hashed_password = user_data[0].get("hashed_password", "")
        #get password salt from db
        password_salt = user_data[0].get("salt", "")
        #check entered password against hashed password + salt
        if check_pwd(password, hashed_password, password_salt) == False:
                print("Wrong password")
                response = redirect("/login")
                response.delete_cookie("session_id")
                return response
        #set session id
        session_id = str(uuid.uuid4())
        #open session collection
        session_collection = session_db.session_collection
        #insert the user into the session_db
        session_collection.delete_one({"session_id": session_id})
        session_data = {"session_id": session_id, "user": user}
        session_collection.insert_one(session_data)
        response = redirect("/quotes")
        response.set_cookie("session_id", session_id)
        return response

@app.route("/login", methods=["GET"])
def get_login():
        session_id = request.cookies.get("session_id", None)
        print("Pre-login session id is:", session_id)
        if session_id:
                return redirect("/quotes")
        return render_template("login.html")

##################
# Registration
##################

@app.route("/register", methods=["POST"])
def post_register():
        #get user input for username and password; double check password is same
        user = request.form.get("user", "")
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        #if passwords are not identical, redirect back to registration page
        if password != password2:
                response = redirect("/register")
                response.delete_cookie("session_id")
                return response
        #open user collection
        user_collection = user_db.user_collection
        #get the user from the form input field
        user_data = list(user_collection.find({"user": user}))
        #if there is no user data present in the db, add the user to the db
        if len(user_data) == 0:
                hashed_password, salt = hash_pwd(password)
                user_data = {"user": user, "hashed_password": hashed_password, "salt": salt}
                user_collection.insert_one(user_data)
                print("User data is:",user_data)
        else:
                print("user already exists")
        response = redirect("/login")
        response.delete_cookie("session_id")
        return response

@app.route("/register", methods=["GET"])
def get_register():
        session_id = request.cookies.get("session_id", None)
        print("Pre-login session id is:", session_id)
        if session_id:
                return redirect("/quotes")
        return render_template("register.html")

##################
# Get User and Public Quotes
##################

@app.route("/quotes", methods=["POST"])
def post_search():
        #get number of visits via cookie; cookies always strings so cast to int
        number_of_visits = int(request.cookies.get("number_of_visits", "0"))
        #request the user's session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist, redirect to the login page
        if not session_id:
                response = redirect("/login")
                return response
        #open a session collection
        session_collection = session_db.session_collection
        #find and list session data
        session_data = list(session_collection.find({"session_id": session_id}))
        #if the session id does not exist in the db, logout user since they are not valid user
        if len(session_data) == 0:
                response = redirect("/logout")
                return response
        #assert that the session data exists before proceding
        assert len(session_data) == 1
        #set session data to the first record
        session_data = session_data[0]
        #getting session information from the session data variable
        user = session_data.get("user", "unknown user")
        #get substring to search for in db
        search = request.form.get("search", "")
        print("search: ")
        print(search)
        # open a quotes collection from the db
        quotes_collection = quotes_db.quotes_collection
        userData = list(quotes_collection.find({"owner": user, "text": {"$eq": search}}))
        publicData = list(quotes_collection.find({"owner": {"$nin": [user]}, "public": True, "text": {"$eq": search}}))
        favorite = list(quotes_collection.find({"favorite": True}))
        #set item id and object id for each quote of the owner's and public quotes
        for item in userData + publicData:
                item["_id"] = str(item["_id"])
                item["object"] = ObjectId(item["_id"])
        #render the quotes page with the data retrieved from above
        html = render_template("quotes.html", data=userData, public=publicData, number_of_visits=number_of_visits, session_id=session_id, user=user, favorite=favorite)
        response = make_response(html)
        response.set_cookie("number_of_visits", str(number_of_visits))
        response.set_cookie("session_id", str(session_id))
        return response

@app.route("/", methods=["GET"])
@app.route("/quotes", methods=["GET"]) 
def get_quotes():
        #get number of visits via cookie; cookies always strings so cast to int
        number_of_visits = int(request.cookies.get("number_of_visits", "0"))
        #request the user's session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist, redirect to the login page
        if not session_id:
                response = redirect("/login")
                return response
        #open a session collection
        session_collection = session_db.session_collection
        #find and list session data
        session_data = list(session_collection.find({"session_id": session_id}))
        #if the session id does not exist in the db, logout user since they are not valid user
        if len(session_data) == 0:
                response = redirect("/logout")
                return response
        #assert that the session data exists before proceding
        assert len(session_data) == 1
        #set session data to the first record
        session_data = session_data[0]
        #getting session information from the session data variable
        user = session_data.get("user", "unknown user")
        # open a quotes collection from the db
        quotes_collection = quotes_db.quotes_collection
        data = list(quotes_collection.find({"owner": user}))
        public_quotes = list(quotes_collection.find({"owner": {"$nin": [user]}, "public": True}))
        favorite = list(quotes_collection.find({"favorite": True}))
        #set item id and object id for each quote of the owner's and public quotes
        for item in data + public_quotes:
                item["_id"] = str(item["_id"])
                item["object"] = ObjectId(item["_id"])
        #render the quotes page with the data retrieved from above
        html = render_template("quotes.html", data=data, public_quotes=public_quotes, number_of_visits=number_of_visits, session_id=session_id, user=user, favorite=favorite)
        response = make_response(html)
        response.set_cookie("number_of_visits", str(number_of_visits + 1))
        response.set_cookie("session_id", str(session_id))
        return response

##################
# Create Quotes
##################

@app.route("/create", methods=["GET"])
def get_create_quotes():
        #get the session id from the cookier
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist, redirect to login
        if not session_id:
                response = redirect("/login")
                return response
        return render_template("create.html")

@app.route("/create", methods=["POST"])
def post_quotes():
        #get the session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist, redirect to login
        if not session_id:
                response = redirect("/login")
                return response
        #open session collection db
        session_collection = session_db.session_collection
        #get session data from the db
        session_data = list(session_collection.find({"session_id": session_id}))
        #if the session data does not exist in the session collection db, redirect to logout since user does not exist
        if len(session_data) == 0:
                response = redirect("/logout")
                return response
        #assert the length of the session data field to be one entry
        assert len(session_data) == 1
        #set session data variable to the first index of session_data
        session_data = session_data[0]
        #get user information from the session data
        user = session_data.get("user", "unknown user")
        text = request.form.get("text", "")
        author = request.form.get("author", "")
        public = request.form.get("public", "") == "on"
        favorite = request.form.get("favorite", "") == "on"
        allow_comments = request.form.get("allow_comments", "") == "on"
        quoteDate = str(date.today())
        if text != "" and author != "":
                #opening quotes db
                quotes_collection = quotes_db.quotes_collection
                #inserting quote into the quotes db
                quotes_data = {"owner": user, "text": text, "author": author, "public": public, "favorite": favorite, "allow_comments": allow_comments, "date": quoteDate}
                quotes_collection.insert_one(quotes_data)
        return redirect("/quotes")

##################
# Comment User Quotes
##################

#GET Comments and Display Quote with Comments
@app.route("/comment/<id>", methods=["GET"])
def get_comments(id=None):
        #get session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist or there is none, redirect to login page
        if not session_id:
                    response = redirect("/login")
                    return response
        #open session collection db
        session_collection = session_db.session_collection
        #get session data from the db
        session_data = list(session_collection.find({"session_id": session_id}))
        #if the session data does not exist in the session collection db, redirect to logout since user does not exist
        if len(session_data) == 0:
                response = redirect("/logout")
                return response
        #assert the length of the session data field to be one entry
        assert len(session_data) == 1
        #set session data variable to the first index of session_data
        session_data = session_data[0]
        #get user information from the session data
        user = session_data.get("user", "unknown user")
        #checking valid quote id
        if id:    
                quotes_collection  = quotes_db.quotes_collection
                data = quotes_collection.find_one({"_id": ObjectId(id)})
                quote_owner = data["owner"]
                data["id"] = str(data["_id"])
                #open collection
                comments_collection = comments_db.comments_collection
                #list comments
                comments = list(comments_collection.find({"quote_id": ObjectId(id)}))
                return render_template("comments.html", data=data, comments=comments, user=user, quote_owner=quote_owner)
        else:
                print("Not a valid id")

#GET Add Comments Page
@app.route("/add-comment/<id>", methods=["GET"])
def get_add_comments(id=None):
         #get session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist or there is none, redirect to login page
        if not session_id:
                    response = redirect("/login")
                    return response
        #checking valid quote id
        if id:    
                quotes_collection = quotes_db.quotes_collection
                data = quotes_collection.find_one({"_id": ObjectId(id)})
                data["id"] = str(data["_id"])
                return render_template("/add-comment.html", data=data)
        else:
                print("Not a valid id")

#POST Add comment to quote
@app.route("/add-comment", methods=["POST"])
def post_comment():
        #get session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist or there is none, redirect to login
        if not session_id:
                response = redirect("/login")
                return response
        #open session collection db
        session_collection = session_db.session_collection
        #get session data from the db
        session_data = list(session_collection.find({"session_id": session_id}))
        #if the session data does not exist in the session collection db, redirect to logout since user does not exist
        if len(session_data) == 0:
                response = redirect("/logout")
                return response
        #assert the length of the session data field to be one entry
        assert len(session_data) == 1
        #set session data variable to the first index of session_data
        session_data = session_data[0]
        #get user information from the session data
        user = session_data.get("user", "unknown user")
        #get the id to use as input to the comments db
        id = request.form.get("_id", None)
        #find comment in form
        comment_to_add = request.form.get("comment","")
        if id:  
                if comment_to_add != "":
                        print("Comment to add is: ", comment_to_add)
                        #open collection
                        comments_collection = comments_db.comments_collection
                        comment_data = {"quote_id": ObjectId(id), "owner": user, "comment": comment_to_add}
                        comments_collection.insert_one(comment_data)
                else:
                        print("No comment to add")
        else:
                print("Not a valid object id")
        return redirect("/quotes")

##################
# Delete User Comments
##################

@app.route("/delete-comment", methods=["GET"])
@app.route("/delete-comment/<comment_id>", methods=["GET"])
def get_delete_comment(comment_id=None):  
        #get session id from cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id doesnt exist, redirect to login
        if not session_id:
                return redirect("/login")
        #if the comment id is valid
        if comment_id:
                #open comments collection
                comments_collection = comments_db.comments_collection
                #find the comment associated with the id
                comment = comments_collection.find_one({"_id": ObjectId(comment_id)})
                #if the comment exists
                if comment:      
                        #allow deletion, check for owner or comment creator is done in above get_comment method
                        comments_collection.delete_one({"_id": ObjectId(comment_id)})
                        print("Comment deleted successfully")
                else:
                       #otherwise comment does not exist
                       print("Comment not found") 
        else:
                #othewise the request is not valid
                print("Invalid request")

        return redirect("/quotes")
        
##################
# Edit User Quotes
##################

@app.route("/edit/<id>", methods=["GET"])
def get_edit(id=None):
        #get session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist or there is none, redirect to login
        if not session_id:
                response = redirect("/login")
                return response
        #if the id does exist, open the quotes collection
        if id:  
                #open collection
                quotes_collection = quotes_db.quotes_collection
                #find quote by ObjectId
                data = quotes_collection.find_one({"_id": ObjectId(id)})
                #check for checkbox values of public and favorite 
                data["public"] = "on" if data.get("public") else "off"
                data["favorite"] = "on" if data.get("favorite") else "off"
                #return json as string
                data["id"] = str(data["_id"])
                return render_template("/edit.html", data=data)
        return render_template("/quotes.html")

@app.route("/edit", methods=["POST"])
def post_edit():
        #get session id from the cookie
        session_id = request.cookies.get("session_id", None)
        #if the session id does not exist or there is none, redirect to login
        if not session_id:
                response = redirect("/login")
                return response
        #get the id, quote text, and quote author
        _id = request.form.get("_id", None)
        text = request.form.get("quote", "")
        author = request.form.get("author", "")
        comment = request.form.get("comment", "")
        public = request.form.get("public", "") == "on"
        favorite = request.form.get("favorite", "") == "on"
        #if the object id exists
        if _id:
                # Open collection
                quotes_collection = quotes_db.quotes_collection
                # Update the values associated with this particular ObjectId
                values = {"$set": {"text": text, "author": author, "comment": comment, "public": public, "favorite": favorite}}
                data = quotes_collection.update_one({"_id": ObjectId(_id)}, values)
                if data.modified_count > 0:
                        print("Quote updated successfully.")
                else:
                        print("Update unsuccessful.")

        # Return to quotes page
        return redirect("/quotes")

##################
# Delete User Quotes
##################

@app.route("/delete", methods=["GET"])
@app.route("/delete/<id>", methods=["GET"]) 
def get_delete(id=None):
        session_id = request.cookies.get("session_id", None)
        if not session_id:
                response = redirect("/login")
                return response
         # delete a quote
        if id:
                #open collection
                quotes_collection = quotes_db.quotes_collection
                #delete the item
                quotes_collection.delete_one({"_id":ObjectId(id)})
                

        return redirect("/quotes")
       
#run flask --app flaskIntro run 