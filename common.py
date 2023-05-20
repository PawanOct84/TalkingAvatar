
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, Attachment, FileContent, FileName, FileType
import base64

from threading import Thread
# Create your views here.



# method for updating
def postpone(function):
  def decorator(*args, **kwargs):
    t = Thread(target = function, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
  return decorator

# sendgrid_api_key='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'
sendgrid_api_key='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'

@postpone
def send_email(to_emails,subject,html_content,store_sandgrid_apikey=None,store_from_email=None,store_from_name=None,file_path=None,file_name=None):
	## from_email should be verified in sandgrid
	## to verified emai go to https://app.sendgrid.com/settings/sender_auth/senders and create senders and verify
	# from_email=settings.ADMIN_EMAIL
	from_name='amitkumar.sinha@navsoft.in'
	if store_from_email:
		from_email = 'amitkumar.sinha@navsoft.in'
	if store_from_name:
		from_name='amitkumar.sinha@navsoft.in'
	message = Mail(
		from_email=from_name, #From(from_email,from_name),
		to_emails= to_emails,
		subject=subject,
		html_content=html_content
	)
	if file_path:
		with open(file_path, 'rb') as f:
			data = f.read()
			f.close()
		encoded = base64.b64encode(data).decode()
		attachment = Attachment()
		attachment.file_content = FileContent(encoded)
		attachment.file_type = FileType('application/pdf')
		attachment.file_name = FileName(str(file_name)+'.pdf')
		message.attachment = attachment
	try:
		if store_sandgrid_apikey:
			sg = SendGridAPIClient(store_sandgrid_apikey)
		else:
			sg = SendGridAPIClient(sendgrid_api_key)
		response = sg.send(message)
		# print("here")
		# print(response.status_code)
		# print(response.body)
		# print(response.headers)
	except Exception as e:
		# print("exception")
		print(str(e))
		print("email not sent")

	return True
