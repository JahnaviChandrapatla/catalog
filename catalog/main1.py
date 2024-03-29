from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup1 import Base, GmailUser, Television, Tvlist
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///television.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Television"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
tvs_tv = session.query(Television).all()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    tvs_tv = session.query(Television).all()
    tvcs = session.query(Tvlist).all()
    return render_template('login.html',
                           STATE=state, tvs_tv=tvs_tv, tvcs=tvcs)
    '''return render_template('myhome.html', STATE=state
    tvs_tv=tvs_tv,tvcs=tvcs)'''


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        rose = make_response(json.dumps('Invalid state parameter.'), 401)
        rose.headers['Content-Type'] = 'application/json'
        return rose
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        erif_oauth_flow = flow_from_clientsecrets(
            'client_secrets.json', scope='')
        erif_oauth_flow.redirect_uri = 'postmessage'
        credentials = erif_oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        rose = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        rose.headers['Content-Type'] = 'application/json'
        return rose

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        rose = make_response(json.dumps(result.get('error')), 500)
        rose.headers['Content-Type'] = 'application/json'
        return rose

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        rose = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        rose.headers['Content-Type'] = 'application/json'
        return rose

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        rose = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        rose.headers['Content-Type'] = 'application/json'
        return rose

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        rose = make_response(json.dumps(
            'Current user already connected.'), 200)
        rose.headers['Content-Type'] = 'application/json'
        return rose

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createGmailUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createGmailUser(login_session):
    User1 = GmailUser(name=login_session['username'], email=login_session[
                   'email'])
    session.add(User1)
    session.commit()
    user = session.query(GmailUser).filter_by(
        email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(GmailUser).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(GmailUser).filter_by(email=email).one()
        return user.id
    except Exception as error:
        print(error)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


# Home


@app.route('/')
@app.route('/home')
def home():
    tvs_tv = session.query(Television).all()
    return render_template('myhome.html', tvs_tv=tvs_tv)


# Tv Category for admins


@app.route('/Televisions')
def Televisions():
    '''It shows the televisions home page
        in this itemcatalogue project'''
    try:
        if login_session['username']:
            name = login_session['username']
            tvs_tv = session.query(Television).all()
            ttc = session.query(Television).all()
            tvcs = session.query(Tvlist).all()
            return render_template('myhome.html', tvs_tv=tvs_tv,
                                   ttc=ttc, tvcs=tvcs, uname=name)
    except:
        return redirect(url_for('showLogin'))


# Showing tvs based on tv category


@app.route('/Televisions/<int:tvid>/AllTvCompanys')
def showTelevision(tvid):
    '''This will show the telivision and applied styles'''
    tvs_tv = session.query(Television).all()
    ttc = session.query(Television).filter_by(id=tvid).one()
    tvcs = session.query(Tvlist).filter_by(televisionid=tvid).all()
    try:
        if login_session['username']:
            return render_template('showTelevision.html', tvs_tv=tvs_tv,
                                   ttc=ttc, tvcs=tvcs,
                                   uname=login_session['username'])
    except:
        return render_template('showTelevision.html',
                               tvs_tv=tvs_tv, ttc=ttc, tvcs=tvcs)

# Add New Tv


@app.route('/Televisions/addTelevision', methods=['POST', 'GET'])
def addTelevision():
    '''This is used to add the tv catagory'''
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        tvcompany = Television(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(tvcompany)
        session.commit()
        return redirect(url_for('Televisions'))
    else:
        return render_template('addTelevision.html', tvs_tv=tvs_tv)


# Edit Tv Category


@app.route('/Televisions/<int:tvid>/edit', methods=['POST', 'GET'])
def editTvCategory(tvid):
    '''This is used to edit the catogory'''
    editTv = session.query(Television).filter_by(id=tvid).one()
    creator = getUserInfo(editTv.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Television name."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('Televisions'))
    if request.method == "POST":
        if request.form['name']:
            editTv.name = request.form['name']
        session.add(editTv)
        session.commit()
        flash("Tv catogory Edited Successfully")
        return redirect(url_for('Televisions'))
    else:
        # tvs_tv is global variable we can them in entire application
        return render_template('editTvCategory.html',
                               ts=editTv, tvs_tv=tvs_tv)

# Delete Tv Category


@app.route('/Televisions/<int:tvid>/delete', methods=['POST', 'GET'])
def deleteTvCategory(tvid):
    '''This is used to delete the catogory'''
    ts = session.query(Television).filter_by(id=tvid).one()
    creator = getUserInfo(ts.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Television."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('Televisions'))
    if request.method == "POST":
        session.delete(ts)
        session.commit()
        flash("Tv Category Deleted Successfully")
        return redirect(url_for('Televisions'))
    else:
        return render_template('deleteTvCategory.html', ts=ts, tvs_tv=tvs_tv)

# Add New Tv Details


@app.route('/Televisions/addTvCompany/addTvDetails/<string:tsname>/add',
           methods=['GET', 'POST'])
def addTvDetails(tsname):
    '''this is used to add the tvlist'''
    ttc = session.query(Television).filter_by(name=tsname).one()
    # See if the logged in user is not the owner of tv
    creator = getUserInfo(ttc.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new television details"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showTelevision', tvid=ttc.id))
    if request.method == 'POST':
        tvtypes = request.form['tvtypes']
        description = request.form['description']
        price = request.form['price']
        rating = request.form['rating']
        inches = request.form['inches']
        tvdetails = Tvlist(
            tvtypes=tvtypes, description=description, price=price,
            rating=rating, inches=inches,
            date=datetime.datetime.now(),
            televisionid=ttc.id,
            user_id=login_session['user_id'])
        session.add(tvdetails)
        session.commit()
        return redirect(url_for('showTelevision', tvid=ttc.id))
    else:
        return render_template('addTvDetails.html',
                               tsname=ttc.name, tvs_tv=tvs_tv)

# Edit Tv details


@app.route('/Televisions/<int:tvid>/<string:tvcname>/edit',
           methods=['GET', 'POST'])
def editTv(tvid, tvcname):
    '''This is used to edit the tvlist'''
    ts = session.query(Television).filter_by(id=tvid).one()
    tvdetails = session.query(Tvlist).filter_by(tvtypes=tvcname).one()
    # See if the logged in user is not the owner of tv
    creator = getUserInfo(ts.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this tvlist"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showTelevision', tvid=ts.id))
    # POST methods
    if request.method == 'POST':
        tvdetails.tvtypes = request.form['tvtypes']
        tvdetails.description = request.form['description']
        tvdetails.price = request.form['price']
        tvdetails.rating = request.form['rating']
        tvdetails.inches = request.form['inches']
        tvdetails.date = datetime.datetime.now()
        session.add(tvdetails)
        session.commit()
        flash("tv Edited Successfully")
        return redirect(url_for('showTelevision', tvid=tvid))
    else:
        return render_template('editTv.html',
                               tvid=tvid, tvdetails=tvdetails, tvs_tv=tvs_tv)

# Delte Tv Edit


@app.route('/Televisions/<int:tvid>/<string:tvcname>/delete',
           methods=['GET', 'POST'])
def deleteTv(tvid, tvcname):
    '''This is used to delete the tvlist'''
    ts = session.query(Television).filter_by(id=tvid).one()
    tvdetails = session.query(Tvlist).filter_by(tvtypes=tvcname).one()
    # See if the logged in user is not the owner of tv
    creator = getUserInfo(ts.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this telivision details"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showTelevision', tvid=ts.id))
    if request.method == "POST":
        session.delete(tvdetails)
        session.commit()
        flash("Deleted list Successfully")
        return redirect(url_for('showTelevision', tvid=tvid))
    else:
        return render_template('deleteTv.html',
                               tvid=tvid, tvdetails=tvdetails, tvs_tv=tvs_tv)

# Logout from current user


@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        rose = make_response(
            json.dumps('Current user not connected....'), 401)
        rose.headers['Content-Type'] = 'application/json'
        return rose
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={
                      'content-type': 'application/x-www-form-urlencoded'})[0]

    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        rose = make_response(
            json.dumps('Successfully disconnected user..'), 200)
        rose.headers['Content-Type'] = 'application/json'
        flash("Successful logged out")
        return redirect(url_for('showLogin'))
        # return rose
    else:
        rose = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        rose.headers['Content-Type'] = 'application/json'
        return rose


# Json
@app.route('/Televisions/JSON')
def allTvsJSON():
    tvcategories = session.query(Television).all()
    category_dict = [c.serialize for c in tvcategories]
    for c in range(len(category_dict)):
        tvs = [i.serialize for i in session.query(
                 Tvlist).filter_by(televisionid=category_dict[c]["id"]).all()]
        if tvs:
            category_dict[c]["tv"] = tvs
    return jsonify(Television=category_dict)


@app.route('/Televisions/tvCatogories/JSON')
def categoriesJSON():
    tvs = session.query(Television).all()
    return jsonify(tvCategories=[c.serialize for c in tvs])


@app.route('/Televisions/tvs/JSON')
def itemsJSON():
    items = session.query(Tvlist).all()
    return jsonify(tvs=[i.serialize for i in items])


@app.route('/Televisions/<path:tvlist_name>/tvs/JSON')
def categoryItemsJSON(tvlist_name):
    tvCategory = session.query(Television).filter_by(name=tvlist_name).one()
    tvs = session.query(Tvlist).filter_by(television=tvCategory).all()
    return jsonify(tvEdtion=[i.serialize for i in tvs])


@app.route('/Televisions/<path:tvlist_name>/<path:edition_name>/JSON')
def ItemJSON(tvlist_name, edition_name):
    tvCategory = session.query(Television).filter_by(name=tvlist_name).one()
    tvEdition = session.query(Tvlist).filter_by(
           tvtypes=edition_name, television=tvCategory).one()
    return jsonify(tvEdition=[tvEdition.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='127.0.0.1', port=9494)
