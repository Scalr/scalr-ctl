#coding:utf-8

def sign_http_request_v3(data, key_id, access_key, timestamp=None):
	date = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", timestamp or time.gmtime())
	data['TimeStamp']=date
	canonical_string = 	"%s:%s:%s" % (data['Action'], key_id, data['TimeStamp'])
	digest = hmac.new(access_key, canonical_string, hashlib.sha256).digest()
	sign = binascii.b2a_base64(digest).strip()
	return sign, date