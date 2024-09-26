from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import User, PasswordResetCode
from .serializers import UserInfoSerializer
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.utils.crypto import get_random_string
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import send_password_reset_code
from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

@swagger_auto_schema(
    method='post',
    operation_description="Register a new user by providing the required fields.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
            'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Password'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Confirm password'),
            'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description='Profile image (optional)', nullable=True),
        },
        required=['email', 'first_name', 'last_name', 'password', 'confirm_password']
    ),
    responses={
        201: openapi.Response(
            description="User registered successfully",
            examples={
                "application/json": {
                    "success": "Account created successfully",
                    "tokens": {
                        "access": "jwt_access_token",
                        "refresh": "jwt_refresh_token"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                "application/json": {"error": "Some error message, e.g. Passwords do not match"}
            }
        )
    }
)
@api_view(['POST'])
def Register(request):

    # get payload
    # username = request.POST.get('username')
    email = request.data.get('email')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')
    profile_image = request.FILES.get('profile_image')

    # make sure all fields are filled
    if not (email and phone and password and confirm_password and first_name and last_name):
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # check if user with email exists
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if passwords match
    if password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
    
    # check password length
    if len(password) <= 5:
        return Response({"error": "Password must be greater than 5 characters"}, status=status.HTTP_400_BAD_REQUEST)
    
    # create user account
    new_user = User(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )
    new_user.set_password(password)

    if profile_image:
        new_user.profile_image = profile_image

    # generate new access and refresh tokens 
    tokens = new_user.tokens()

    response = {
        "success": "Account created successfully",
        "tokens": tokens
    }

    return Response(response, status=status.HTTP_201_CREATED)

class MyTokenObtainPairView(TokenObtainPairView):

    serializer_class = TokenObtainPairSerializer

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Token obtained successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='Access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized - Account is inactive."),
        },
        operation_description=(
            "Obtain a new access and refresh token pair using valid credentials. The user must have an active account "
            "to successfully log in. Use the Bearer token in the `Authorization` header for accessing endpoints that require authentication."
        ),
        operation_summary="Login - Obtain JWT Token Pair",
        security=[]
    )
    def post(self, request, *args, **kwargs):
        # Extract credentials from the request
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate user with provided credentials
        user = authenticate(request, username=email, password=password)
        
        # Check if user is authenticated and active
        if user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"error": "Account is inactive. Please verify your email to activate your account."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Proceed with the parent method to handle token generation
        try:
            response = super().post(request, *args, **kwargs)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        # return tokens
        return response

class MyTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    @swagger_auto_schema(
        request_body=TokenRefreshSerializer,
        responses={
            200: openapi.Response(
                description="Token refresh successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='New access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
                    }
                )
            ),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Token is blacklisted"),
                        'code': openapi.Schema(type=openapi.TYPE_STRING, description="token_not_valid"),
                    },
                    example={
                        "detail": "Token is blacklisted",
                        "code": "token_not_valid"
                    }
                )
            ),
        },
        operation_description=(
            "Refresh an access token using a valid refresh token. The access token is valid for 10 minutes, "
            "and the refresh token is valid for 2 weeks (14 days)."
        ),
        operation_summary="Refresh Token",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs) 
    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description='Refresh token of the current session that needs to be blacklisted.'
            ),
        },
        required=['refresh'],
        example={
            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
        },
    ),
    responses={
        204: openapi.Response(
            description="Successfully logged out.",
            examples={
                'application/json': {
                    'message': 'Successfully logged out.'
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request",
            examples={
                'application/json': {
                    'error': 'Refresh token is required.'
                }
            }
        ),
    },
    operation_description=(
        "Logs out the current user by invalidating the provided refresh token. This action blacklists the refresh token, "
        "ensuring that it cannot be used to obtain new access tokens in the future. The refresh token must be included "
        "in the request body. If the token is missing or invalid, a 400 Bad Request error will be returned."
    ),
    operation_summary="Logout",
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def Logout(request):
    
    try:
        # Extract the refresh token from the request data
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Blacklist the refresh token to prevent further use
        token = RefreshToken(refresh_token)
        token.blacklist()

        # Return a response indicating successful logout
        return Response({"message": "Successfully logged out."}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        # Return a response in case of any exceptions during the process
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="User information retrieved successfully",
            schema=UserInfoSerializer
        ),
        401: openapi.Response(
            description="Unauthorized",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Error detail"),
                },
                example={
                    "detail": "Authentication credentials were not provided."
                }
            )
        ),
    },
    operation_description="Retrieve the current authenticated user's information.",
    operation_summary="Get User Info",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def GetUserInfo(request):
    user = request.user
    serializer = UserInfoSerializer(user)

    response_data = serializer.data
    response_data["uploaded_profile_image"] = user.profile_image_url()
    return Response(response_data)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address'),
        }
    ),
    responses={
        200: openapi.Response(description="Reset code sent successfully"),
        400: openapi.Response(description="Bad Request"),
    },
    operation_description="Request a password reset code by entering your email address.",
    operation_summary="Request Password Reset Code",
)
@api_view(['POST'])
def RequestResetCode(request):
    email = request.data.get('email')
    if email and User.objects.filter(email=email).exists():
        try:
            user = User.objects.get(email=email)

            # delete old codes
            PasswordResetCode.objects.filter(user=user).delete()

            code = get_random_string(length=6, allowed_chars='0123456789')
            PasswordResetCode.objects.create(user=user, code=code)

            # Send email (this is a simple example; configure your email backend as needed)
            send_password_reset_code(user.email, code)

            return Response({"detail": "Reset code sent successfully"}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "Email not found"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"error": "Email is invalid"}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            'code': openapi.Schema(type=openapi.TYPE_STRING, description='Reset code sent to email'),
        },
        required=['email', 'code']
    ),
    responses={
        200: openapi.Response(description="Reset code is valid."),
        400: openapi.Response(description="Invalid email, reset code, or reset code has expired.")
    },
    operation_description="Verify the reset code sent to the user's email.",
    operation_summary="Verify Reset Code"
)
@api_view(['POST'])
def VerifyResetCode(request):
    email = request.data.get('email')
    code = request.data.get('code')

    try:
        user = User.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(user=user, code=code)

        if reset_code.is_valid():
            return Response({"message": "Reset code is valid."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Reset code has expired."}, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        return Response({"message": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
    except PasswordResetCode.DoesNotExist:
        return Response({"message": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['code', 'password', 'confirm_password'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            'code': openapi.Schema(type=openapi.TYPE_STRING, description='The reset code sent to the user email.'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='The new password.'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description='The new password again for confirmation.'),
        },
    ),
    responses={
        200: openapi.Response(description="Password reset successfully."),
        400: openapi.Response(description="Bad Request: Invalid input or expired code."),
    },
    operation_description="Reset the user's password using the reset code.",
    operation_summary="Reset Password",
)
@api_view(['POST'])
def ResetPassword(request):
    email = request.data.get('email')
    code = request.data.get('code')
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    # Check if passwords match
    if password != confirm_password:
        return Response({"detail": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if password length is greater than 5
    if len(password) <= 5:
        return Response({"detail": "Password must be greater than 5 characters."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(code=code, user=user)
        
        # Verify if the code is still valid
        if not reset_code.is_valid():
            return Response({"detail": "Reset code is expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        # Optionally delete the used reset code
        reset_code.delete()

        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)

    except PasswordResetCode.DoesNotExist:
        return Response({"detail": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)
    

@swagger_auto_schema(
    method='post',
    operation_description="Update user profile settings including username, email, phone, password, and profile image.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Email address'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
            'vehicle_type': openapi.Schema(type=openapi.TYPE_STRING, description='Vehicle type'),
            'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='New password'),
            'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Confirm new password'),
            'profile_image': openapi.Schema(type=openapi.TYPE_FILE, description='Profile image'),
        },
        required=[]
    ),
    responses={
        200: openapi.Response(
            description="Profile updated successfully",
            examples={
                "application/json": {
                    "success": "Password updated"
                }
            }
        ),
        400: openapi.Response(
            description="Bad request due to missing or invalid input",
            examples={
                "application/json": {"error": "Some error message"}
            }
        )
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ProfileSetting(request):

    # get payload
    username = request.POST.get('username')
    email = request.POST.get('email')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    vehicle_type = request.POST.get('vehicle_type')
    phone = request.POST.get('phone')
    password = request.POST.get('password')
    confirm_password = request.POST.get('confirm_password')
    profile_image = request.FILES.get('profile_image')

    user = request.user

    # make sure payload contains data
    if not (username or email or first_name or last_name or vehicle_type or phone or profile_image): 
        return Response({"error": "Empty form paylaod"}, status=status.HTTP_400_BAD_REQUEST)
    
    # validate email
    if password and confirm_password:
        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) <= 5:
            return Response({"error": "Password must be greater than 5 characters"}, status=status.HTTP_400_BAD_REQUEST)
        
        # update user password
        user.set_password(password)

    # update user data
    if username and username != user.username: 
        user.username = username
    
    if email and email!= user.email:
        user.email = email

    if first_name and first_name!= user.first_name:
        user.first_name = first_name

    if last_name and last_name!= user.last_name:
        user.last_name = last_name

    if vehicle_type and vehicle_type!= user.vehicle_type:
        user.vehicle_type = vehicle_type

    if phone and phone!= user.phone:
        user.phone = phone

    if profile_image:
        user.profile_image = profile_image

    user.save()
    return Response({"success": "Password updated"}, status=status.HTTP_200_OK)