from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from settings import Setting
from model import Cotton, PredictDate, Name, db
from datetime import datetime, timedelta
from app import app

setting = Setting()
line_bot_api = LineBotApi(setting.channel_token)
handler = WebhookHandler(setting.channel_secret)

db.init_app(app)


def get_data():
    with app.app_context():
        predict_dates = PredictDate.query.all()
        if predict_dates:
            for _item in predict_dates:
                name = Name.query.filter_by(user_id=_item.user_id).first()

                today = datetime.utcnow() + timedelta(hours=8)
                calculate_day = _item.predict_date.replace(tzinfo=None) - today.replace(tzinfo=None)

                if 5 > calculate_day.days >= 0:
                    text = f"親愛的 {name.name} 您好\n"
                    text += f"您的生理期預計於 {abs(calculate_day.days) + 1} 天內到來 \n"

                elif 0 > calculate_day.days > -5:
                    text = f"您的生理期可能已經開始，預測日為 {_item.predict_date.strftime('%Y-%m-%d')}"

                # 讀取衛生棉存量，並判斷安全存量
                save_message = "棉棉庫存量足夠"
                danger_message = "以下種類的棉棉可能不足："
                db_cotton: Cotton = Cotton.query.filter_by(user_id=_item.user_id).first()
                category = ["護墊", "日用量少", "日用正常", "日用量多", "夜用正常", "夜用量多"]
                amount = [db_cotton.pad, db_cotton.little_daily, db_cotton.normal_daily,
                          db_cotton.high_daily, db_cotton.normal_night, db_cotton.high_night]

                flag = True
                for _category, _amount in zip(category, amount):
                    if _amount < db_cotton.save_amount:
                        danger_message += f"\n {_category} 剩餘 {_amount} 片"
                        flag = False

                text += save_message if flag else danger_message

                line_bot_api.push_message(to=_item.user_id, messages=TextSendMessage(text=text))


if __name__ == '__main__':
    get_data()
