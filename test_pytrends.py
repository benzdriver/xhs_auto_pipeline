from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)
kw_list = ["Python"]
pytrends.build_payload(kw_list, timeframe='now 7-d', geo='US')
data = pytrends.interest_over_time()
print(data) 