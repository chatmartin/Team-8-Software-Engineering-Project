#The purpose of this file is to build goals for all nutrients for the user based on their bio info

from globals import *

def recommended_goal(username):
    conn = get_db_conn()
    if conn is None:
        return {"err": "ERROR: Unable to access database."}
    with conn.cursor() as cursor:
        query = "SELECT user_id FROM login_info WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return {"err": "ERROR: User not found."}
        user_id = row[0]
        query = "SELECT * FROM user_bio_data WHERE user_id=%s"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        if row is None:
            weight = 70
            height = 170
            age = 40
            gender = 'male'
            body_fat = 25
            activity = 1.2
        else:
            gender = row[1]
            height = row[2]*2.54
            weight = row[3]*0.453592
            body_fat = row[4]
            age = row[5]
            if row[6]== 'sedentary':
                activity = 1.2
            elif row[6] == 'light':
                activity = 1.375
            elif row[6] == 'moderate':
                activity = 1.55
            else:
                activity = 1.725
        if gender=='male':
            bmr = 10*weight+6.25*height-5*age+5
        else:
            bmr = 10*weight+6.25*height-5*age-161
        tdee = (bmr + 370+21.6*(weight*(1-body_fat/100)))*activity
        nutrients = {'calories': tdee, 'protein': (tdee * 0.25) / 4, 'fat': (tdee * 0.3) / 9,
                     'carbohydrates': (tdee * 0.45) / 4, 'saturated fat': tdee * 0.1 / 9, 'sugar': (tdee * 0.1) / 4,
                     'alcohol': 0}
        if gender == 'female':
            nutrients['fiber']=25
        else:
            nutrients['fiber']=38
        nutrients['copper']=0.9
        nutrients['calcium'] = 1.3
        nutrients['sodium'] = 2300
        nutrients['choline'] = 550
        nutrients['cholesterol'] = 300
        nutrients['folate'] = 400
        nutrients['iodine'] = 150
        nutrients['iron'] = 18
        nutrients['magnesium'] = 420
        nutrients['manganese'] = 2.3
        nutrients['phosphorus'] = 1250
        nutrients['potassium'] = 4700
        nutrients['selenium'] = 55
        nutrients['vitamin a'] = 900
        if gender == 'female':
            nutrients['vitamin b1'] = 1.1
            nutrients['vitamin b2'] = 1.1
            nutrients['vitamin b3'] = 14
        else:
            nutrients['vitamin b1'] = 1.2
            nutrients['vitamin b2'] = 1.3
            nutrients['vitamin b3'] = 16
        nutrients['vitamin b5'] = 5
        nutrients['vitamin b6'] = 1700
        nutrients['vitamin b12'] = 2.4
        nutrients['vitamin c'] = 90000
        nutrients['vitamin d'] = 20
        nutrients['vitamin e'] = 15
        nutrients['vitamin k'] = 120
        nutrients['zinc'] = 11
        return nutrients
