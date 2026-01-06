import json
import imagehash
import random
import datetime
from math import radians, sin, cos, sqrt, atan2
from PIL import Image, ExifTags
from django.core.files.storage import default_storage
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Count, Q
from .models import UserData, SubmitProof, Reward, RedeemedReward
from .forms import SubmitProofForm
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

#  Extract GPS from EXIF 
def get_exif_location(img_path):
    try:
        img = Image.open(img_path)
        exif_data = img._getexif()
        if not exif_data:
            return None, None

        gps_info = {}
        for tag, value in exif_data.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_info = value
                break

        def _convert_to_degrees(value):
            try:
                d, m, s = value
                def _to_float(r):
                    return float(r[0]) / float(r[1]) if isinstance(r, tuple) else float(r)
                return _to_float(d) + _to_float(m)/60 + _to_float(s)/3600
            except Exception as e:
                print("Error converting GPS to degrees:", e, value)
                return None

        lat, lon = None, None
        if gps_info:
            gps_lat = gps_info.get(2)
            gps_lat_ref = gps_info.get(1)
            gps_lon = gps_info.get(4)
            gps_lon_ref = gps_info.get(3)
            if gps_lat and gps_lat_ref and gps_lon and gps_lon_ref:
                lat = _convert_to_degrees(gps_lat)
                if lat is not None and gps_lat_ref != "N":
                    lat = -lat
                lon = _convert_to_degrees(gps_lon)
                if lon is not None and gps_lon_ref != "E":
                    lon = -lon
        return lat, lon
    except Exception as e:
        print("EXIF error:", e)
        return None, None

#  Haversine distance 
def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        R = 6371000  # meters
        phi1, phi2 = radians(lat1), radians(lat2)
        d_phi = radians(lat2 - lat1)
        d_lambda = radians(lon2 - lon1)
        a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))
    except Exception as e:
        print("Distance calc error:", e)
        return None

#  LOGOUT 
def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('login')

#  EMAIL CHECK
@csrf_exempt
def check_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        exists = UserData.objects.filter(email=email).exists()
        return JsonResponse({"exists": exists})
    return JsonResponse({"error": "Invalid request"}, status=400)

#  INDEX 
def index(request):
    return render(request, 'mainapp/index.html')

#  LOGIN 
def login_page(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = UserData.objects.get(email=email)
            if check_password(password, user.password):
                request.session.flush()
                request.session['user_email'] = email
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                return redirect('profile')
            else:
                error = "Invalid credentials. Please try again"
                return render(request, 'mainapp/login.html', {'error': error})
        except UserData.DoesNotExist:
            error = "You are not registered yet. Please register first."
            return render(request, 'mainapp/login.html', {'error': error})
    return render(request, 'mainapp/login.html')

#  SIGNUP with OTP 
def signup_page(request):
    if request.method == 'POST':
        name = request.POST['fullname']
        email = request.POST['email']
        password = request.POST['password']
        if UserData.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('signup')

        otp = random.randint(100000, 999999)
        request.session['temp_user'] = {
            'name': name,
            'email': email,
            'password': make_password(password),
            'otp': otp
        }

        try:
            send_mail(
                subject="Green Coin - Email Verification OTP",
                message=f"Your OTP for email verification is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.info(request, "An OTP has been sent to your email. Please verify.")
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")
            return redirect('signup')

        return redirect('verify_otp')
    return render(request, 'mainapp/signup.html')

#  VERIFY OTP 
def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST['otp']
        temp_user = request.session.get('temp_user')
        if temp_user:
            if str(temp_user['otp']) == entered_otp:
                UserData.objects.create(
                    name=temp_user['name'],
                    email=temp_user['email'],
                    password=temp_user['password']
                )
                del request.session['temp_user']
                messages.success(request, "Signup successful! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect('verify_otp')
        else:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect('signup')
    return render(request, 'mainapp/verify_otp.html')

def signup_success(request):
    return render(request, 'mainapp/signup_success.html')

#  SUBMIT PROOF 
def submit_proof(request):
    email = request.session.get('user_email')
    if not email:
        messages.error(request, "Please log in first to submit proof.")
        return redirect('login')
    try:
        user = UserData.objects.get(email=email)
    except UserData.DoesNotExist:
        messages.error(request, "User not found. Please log in again.")
        return redirect('login')

    if request.method == 'POST':
        form = SubmitProofForm(request.POST, request.FILES)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.user = user

            def safe_float(val):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return None

            claimed_lat = safe_float(request.POST.get("claimed_latitude"))
            claimed_lon = safe_float(request.POST.get("claimed_longitude"))
            live_lat = safe_float(request.POST.get("live_latitude"))
            live_lon = safe_float(request.POST.get("live_longitude"))

            uploaded_file = request.FILES["proof_image"]
            temp_filename = default_storage.save("temp/" + uploaded_file.name, uploaded_file)
            full_path = os.path.join(default_storage.location, temp_filename)

            exif_lat, exif_lon = get_exif_location(full_path)

            proof.claimed_latitude = claimed_lat
            proof.claimed_longitude = claimed_lon
            proof.live_latitude = live_lat
            proof.live_longitude = live_lon
            proof.exif_latitude = exif_lat
            proof.exif_longitude = exif_lon

            
            print("Claimed:", claimed_lat, claimed_lon)
            print("Live:", live_lat, live_lon)
            print("EXIF:", exif_lat, exif_lon)

            # Duplicate image check
            try:
                new_hash = imagehash.average_hash(Image.open(full_path))
                last_submission = SubmitProof.objects.filter(user=user).order_by("-submission_date").first()
                if last_submission:
                    old_hash = imagehash.average_hash(Image.open(last_submission.proof_image))
                    if new_hash == old_hash:
                        messages.error(request, " Duplicate image detected! Please upload a new photo.")
                        default_storage.delete(temp_filename)
                        return redirect("submit_proof")
            except Exception as e:
                print("Image hash check error:", e)

            #  DISTANCE LOGIC 
            distance = None
            try:
                lat_ref = claimed_lat if claimed_lat is not None else live_lat
                lon_ref = claimed_lon if claimed_lon is not None else live_lon

                if lat_ref is not None and lon_ref is not None and exif_lat is not None and exif_lon is not None:
                    distance = calculate_distance(lat_ref, lon_ref, exif_lat, exif_lon)

                proof.calculated_distance = distance

                if distance is not None:
                    if distance <= 50:
                        proof.status = "Approved"
                        messages.success(request, f" Proof auto-approved (distance: {int(distance)} m).")
                    else:
                        proof.status = "Rejected"
                        proof.rejection_reason = f"Location mismatch: {int(distance)} meters away."
                        messages.error(request, f" Auto-rejected: {int(distance)} m difference.")
                else:
                    proof.status = "Pending"
                    messages.info(request, "Distance could not be calculated (manual/live/EXIF missing).")
            except Exception as e:
                print("Distance check error:", e)
                proof.status = "Pending"
                proof.calculated_distance = None

            proof.save()
            default_storage.delete(temp_filename)
            messages.success(request, " Proof submitted successfully!")
            return redirect('submit_proof')
        else:
            messages.error(request, "Proof submission failed due to validation errors.")
    else:
        form = SubmitProofForm()
    return render(request, 'mainapp/proof_sub.html', {'form': form})

#  LEADERBOARD 
def update_leaderboard():
    users = UserData.objects.annotate(
        total_submissions=Count('submitproof'),
        solar_panel_count=Count('submitproof', filter=Q(submitproof__activity_type='Solar Panel Installation'))
    ).order_by('-earned_coins', 'total_submissions', '-solar_panel_count', 'id')
    rank = 1
    for user in users:
        user.rank = rank
        user.save()
        rank += 1

def leaderboard(request):
    update_leaderboard()
    users = UserData.objects.all().order_by('rank')
    return render(request, 'mainapp/leaderboard.html', {'users': users})

#  PROFILE 
@never_cache
def profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    try:
        user = UserData.objects.get(id=user_id)
    except UserData.DoesNotExist:
        request.session.flush()
        return redirect('login')

    all_users = UserData.objects.order_by('-earned_coins')
    rank = list(all_users).index(user) + 1
    earned_coins = f" {user.earned_coins}"
    spent_coins = f" {user.spent_coins}"
    coins_left = f" {user.coins_left()}"
    submitted_proofs = SubmitProof.objects.filter(user=user).order_by('-submission_date')
    context = {
        'user': user,
        'earned_coins': earned_coins,
        'spent_coins': spent_coins,
        'coins_left': coins_left,
        'rank': rank,
        'submitted_proofs': submitted_proofs,
    }
    return render(request, 'mainapp/profile.html', context)

#  RESUBMIT PROOF 
def resubmit_proof(request, submission_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    submission = get_object_or_404(SubmitProof, id=submission_id)
    if submission.status != 'Rejected':
        messages.error(request, "Only rejected proofs can be submitted.")
        return redirect('profile')

    if request.method == 'POST' and request.FILES.get('proof_file'):
        new_proof_file = request.FILES['proof_file']
        old_proof_path = submission.proof_image.path
        temp_filename = 'temp/' + new_proof_file.name
        temp_file_path = default_storage.save(temp_filename, new_proof_file)
        full_temp_path = os.path.join(default_storage.location, temp_file_path)
        try:
            old_hash = imagehash.average_hash(Image.open(old_proof_path))
            new_hash = imagehash.average_hash(Image.open(full_temp_path))
            if old_hash == new_hash:
                messages.error(request, "This image appears to be the same as the previously rejected one. Please upload a different image.")
                default_storage.delete(temp_file_path)
                return redirect('resubmit_proof', submission_id=submission.id)
            submission.proof_image = new_proof_file
            submission.status = 'Pending'
            submission.rejection_reason = None
            submission.save()
            messages.success(request, 'Proof resubmitted successfully!')
        except Exception as e:
            messages.error(request, f"Error processing image: {e}")
        finally:
            if default_storage.exists(temp_file_path):
                default_storage.delete(temp_file_path)
        return redirect('profile')
    return render(request, 'mainapp/resubmit_form.html', {'submission': submission})

#  REWARD PAGE 
def reward(request):
    return render(request, 'mainapp/reward.html')

#  REDEEM REWARD 
@csrf_exempt
def redeem_reward(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User not logged in'})
        try:
            data = json.loads(request.body)
            reward_name = data.get('reward')
            reward_cost = int(data.get('cost'))
            user = UserData.objects.get(id=user_id)
            if user.coins_left() >= reward_cost:
                user.spent_coins += reward_cost
                user.save()
                RedeemedReward.objects.create(user=user, reward_name=reward_name, cost=reward_cost)
                return JsonResponse({'success': True, 'remaining_coins': user.coins_left()})
            else:
                return JsonResponse({'success': False, 'message': 'Not enough coins'})
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(traceback_str)
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

#  AWARENESS PAGE
def awareness_page(request):
    return render(request, 'mainapp/awareness.html')
