# from rest_framework_simplejwt.authentication import JWTAuthentication
#
#
# class CustomTokenAuthentication(JWTAuthentication):
#     def get_header(self, request):
#         header = super().get_header(request)
#         if header is None:
#             return None
#
#         if header.startswith(b'Token '):
#             return header.replace(b'Token ', b'Bearer ')
#         return header
