from webtranslator import db

class Webtranslation(db.Model):
    url_num = db.Column(db.Integer, primary_key=True, nullable='false')
    address = db.Column(db.String)
    title = db.Column(db.String)

    def __repr__(self):
        return str(self.address)