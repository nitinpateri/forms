import flask
import datetime
import smtplib
import pymongo
from bson.objectid import ObjectId
import random
import gspread
from google.oauth2.service_account import Credentials
import gc
import pandas as pd
from io import BytesIO 
import openpyxl


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
# using json, creating new set of credentials.
creds= Credentials.from_service_account_file("credentials.json",scopes=scope)
client =gspread.authorize(creds)
def get_or_create_sheet(client, workbook, sheet_name):
    try:
        sheet = workbook.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        sheet = workbook.add_worksheet(title=sheet_name, rows="100", cols="10")
    return sheet
sheet_id="1hM1yu7xksddOnxag3wOhiy2WZ0THXv3iGGUFftkM7ZU"
workbook=client.open_by_key(sheet_id)

sheets=map(lambda x:x.title, workbook.worksheets())
print(list(sheets))

sheet=client.open_by_key(sheet_id).sheet1
app = flask.Flask(__name__)
global username
global passwd
#connection
client = pymongo.MongoClient(
  'mongodb+srv://nitinpateri1:passwd123@cluster0.jmo22.mongodb.net/?retryWrites=true&w=majority'
)
mydb = client['survey']
mycol = mydb['userdata']
#Index Page
@app.route('/')
def index():
    username=0
    passwd=0
    return flask.render_template('index.html')

#Sign in Page
@app.route("/sign-in", methods=['GET', 'POST'])
def login():
    username=0
    passwd=0
    if flask.request.method == 'POST':
        
        mydb = client['survey']
        mycol = mydb['userdata']
        data = mycol.find()
        passwd = flask.request.form['password']
        username = flask.request.form['username']
        global user_login
        user_login = mycol.find()
        for i in user_login:
            if 'username' in i:
                if i['username'] == username:
                    if i['password'] == passwd:
                        return flask.redirect(str(i['_id'])+'/home')
                    else:
                        return flask.render_template("register.html",data=['Incorrect Password or username',2])
            else:
                return flask.render_template("mail.html")
    else:
        return flask.render_template("signin.html")

#Register
@app.route("/register", methods=['GET', 'POST'])
def register():
    if flask.request.method == 'POST':
        passwd = flask.request.form['password']
        username = flask.request.form['username']
        user_login = mycol.find()
        for i in user_login:
            
            if 'username' in i:
                print(i)
                if i['username'] == username:
                    return flask.render_template('register.html',data=[2,'Player already exist'])
                
            
            user = {
                    'username':username,
                    'password':passwd,
                    'forms-created':[],
                    'forms-filled':[],
                }
            r=mycol.insert_one(user)
            return flask.render_template('signin.html')
        return flask.render_template('register.html')
            
    else:
        return flask.render_template('register.html')

#home
@app.route("/<id>/home", methods=['GET', 'POST'])
def home(id):
    data=mycol.find_one({'_id':ObjectId(id)})
    
    if flask.request.method == 'POST':
        pass
    else:
        forms = mydb['forms']
        form_data=forms.find()
        for i in form_data:
            if 'templates' in i:
                templates = i['templates']
        
        forms = mydb['forms']
        form_data=forms.find()
        temp1=[]
        for i in form_data:
            temp=[]
            if 'form-details' in i:
                print(i)
                temp.append(str(i['_id']))
                for j in i['form-details'][0]:
                    print(j)
                    
                    if j['type'] == 'title':
                        temp.append(j['Question'])
            temp1.append(temp)
        return flask.render_template('home.html',data=[templates,temp1,id])



#create Form
@app.route("/<id>/create-form/<template>", methods=['GET', 'POST'])
def create_form(id,template):
    if flask.request.method == 'POST':
        pass
    else:
        data=mycol.find_one({'_id':ObjectId(id)})
        forms = mydb['forms']
        _d = forms.find()
        for i in _d:
            if 'templates' in i:
                if template in i['templates']:
                    form = i['templates'][template]
        temp=0
        for i in _d:
            if 'form-details' in i:
                if id in i['form-details'][0] == form:
                    temp=1
        
        if temp==0:     
            re=forms.insert_one({'form-details':[form,[id]]})
        
        _d = forms.find()
        for i in _d:
            if 'form-details' in i:
                if id in i['form-details'][1]:
                    if str(i['_id']) not in data['forms-created']:
                        data['forms-created'].append(str(i['_id']))
                        mycol.update_one({'_id':ObjectId(id)},{"$set":{'forms-created':data['forms-created']}})
                    return flask.redirect('/'+id+'/'+str(i['_id'])+'/form')

#View Form
@app.route("/<form_id>/viewform", methods=['GET', 'POST'])
def viewforms(form_id):
    if flask.request.method == 'GET':
        forms = mydb['forms']
        form_data=forms.find_one({'_id':ObjectId(form_id)})
        return flask.render_template('viewform.html',data={'data':form_data['form-details'][0]})


@app.route("/<id>/<form_id>/form", methods=['GET', 'POST'])
def edit_form(id,form_id):
    if flask.request.method == 'POST':
        pass
    else:
        data=mycol.find_one({'_id':ObjectId(id)})
        forms = mydb['forms']
        form_data=forms.find_one({'_id':ObjectId(form_id)})
        if 'forms-created' in data:
            if form_id in data['forms-created']:
                return flask.render_template('forms.html',data={'data':form_data['form-details'][0]})
            else:
                return flask.render_template('viewform.html',data={'data':form_data['form-details'][0]})

@app.route("/<id>/<form_id>/<question>/edit", methods=['GET', 'POST'])
def edit_question(id,form_id,question):
    data=mycol.find_one({'_id':ObjectId(id)})
    forms = mydb['forms']
    form_data=forms.find_one({'_id':ObjectId(form_id)})
    for i in form_data:
        if 'form-details' in i:
            for j in form_data['form-details'][0]:
                if j['Question']==question:
                    question_data=j
    notify=0
    if flask.request.method == "POST":
        filtered = flask.request.form.getlist('options')
        for i in filtered:
            if i=='':
                del filtered[filtered.index('')]
        question_data['options']=filtered
        for i in form_data:
            if 'form-details' in i:
                for j in form_data['form-details'][0]:
                    if j['Question']==question :
                        question_data['Question']=flask.request.form['question']
                        try:
                            question_data['type']=flask.request.form['type']
                        except:
                            pass
                        form_data['form-details'][0][form_data['form-details'][0].index(j)]=question_data
                        
                        forms.update_one({'_id':ObjectId(form_id)},{"$set":{'form-details':form_data['form-details']}})
                        notify = 1
                        return flask.redirect('/'+id+'/'+form_id+'/form')
    return flask.render_template('edit-question.html',data={'data':form_data['form-details'][0],'form_id':form_id,'id':data['_id'],'Question':question_data,'notify':notify})

@app.route("/<id>/<form_id>/<question>/delete", methods=['GET', 'POST'])
def delete_question(id,form_id,question):
    forms = mydb['forms']
    form_data=forms.find_one({'_id':ObjectId(form_id)})
    for i in form_data:
            if 'form-details' in i:
                for j in form_data['form-details'][0]:
                    print(j['Question'],question,j['Question']==question)
                    if j['Question']==question :
                        del form_data['form-details'][0][form_data['form-details'][0].index(j)]
            forms.update_one({'_id':ObjectId(form_id)},{"$set":{'form-details':form_data['form-details']}})
    return flask.redirect('/'+id+'/'+form_id+'/form')

@app.route("/<id>/<form_id>/<question>/add", methods=['GET', 'POST'])
def add_question(id,form_id,question):
    data=mycol.find_one({'_id':ObjectId(id)})
    forms = mydb['forms']
    form_data=forms.find_one({'_id':ObjectId(form_id)})
    for i in form_data:
            if 'form-details' in i:
                for j in form_data['form-details'][0]:
                    if j['Question']==question :
                        index=form_data['form-details'][0].index(j)
    if flask.request.method == "POST":
        if flask.request.form['type'] == 'options':
            filtered = flask.request.form.getlist('options')
            for i in filtered:
                if i=='':
                    del filtered[filtered.index('')]
            temp11={'Question':flask.request.form['question'],'type':flask.request.form['type'],'options':filtered}
        else:
            temp11={'Question':flask.request.form['question'],'type':flask.request.form['type']}
        form_data['form-details'][0].insert(index+1,temp11)
        forms.update_one({'_id':ObjectId(form_id)},{"$set":{'form-details':form_data['form-details']}})
        if flask.request.form['type'] == 'options':
            return flask.redirect('/'+id+'/'+form_id+'/'+flask.request.form['question']+'/edit')
        return flask.redirect('/'+id+'/'+form_id+'/form')
    return flask.render_template('edit-question.html',data={'data':form_data['form-details'][0],'id':id,'form_id':form_id,'Question':''})

@app.route("/<id>/<form_id>/submit-response", methods=['GET', 'POST'])
def response(id,form_id):
    if flask.request.method == 'POST':
        forms = mydb['forms']
        form_data=forms.find_one({'_id':ObjectId(form_id)})
        response = flask.request.form.getlist('response')
        dict_response={}
        count = 0
        files = flask.request.files.getlist("response") 
        print(files)
        for file in files:
            print(file)
            if file.filename:  # Check if a file is uploaded
                file.save(f"static/files/{file.filename}")
                print("Saved File:", file.filename)
        for i in form_data['form-details'][0]:
                if i['type']!='title' and i['type']!='h2':
                    dict_response[i['Question']] = response[count]
                    count+=1
        print(dict_response)
        if 'responses' in form_data:
            form_data['responses'].append(dict_response)
        else:
            form_data['responses'] = [dict_response]
        forms.update_one({'_id':ObjectId(form_id)},{"$set":{'responses':form_data['responses']}})
        return flask.redirct('/{{id}}/home')
        
@app.route("/<id>/<form_id>/responses", methods=['GET', 'POST'])
def responses(form_id,id):
    if flask.request.method == 'GET':
        forms = mydb['forms']
        form_data=forms.find_one({'_id':ObjectId(form_id)})
        if 'responses' in form_data:
            return flask.render_template('responses.html',data={'data':form_data['responses'],'form_id':form_id})

@app.route('/<id>/<form_id>/google-sheets', methods=['GET', 'POST'])
def google_sheets(id,form_id):
    if flask.request.method == 'GET':
        forms = mydb['forms']
        form_data=forms.find_one({'_id':ObjectId(form_id)})
        responses=[]
        attribute=[]
        if 'responses' in form_data:
            for i in form_data['responses']:
                for j in i:
                    if j not in attribute:
                        attribute.append(j)
            responses.append(attribute)
            for i in form_data['responses']:
                temp=[]
                for j in range(len(attribute)):
                    temp.append('')
                for j in i:
                    temp[attribute.index(j)]=i[j]
                responses.append(temp)
                break
        for i in responses:
            sheet.append_row(i)
        data = responses

    # Convert list to DataFrame
    df = pd.DataFrame(data)

    excel_io = BytesIO()
    with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")


    excel_io.seek(0)  

    return flask.send_file(
        excel_io,
        as_attachment=True,
        download_name="data.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__=="__main__":
    app.run(host='0.0.0.0', port='8000', debug='True')