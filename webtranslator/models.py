from webtranslator import db

class Webtranslation(db.Model):
    url_num = db.Column(db.NUMERIC, primary_key=True, nullable='false')
    address = db.Column(db.VARCHAR)
    title = db.Column(db.VARCHAR)

    def __repr__(self):
        return str(self.address)