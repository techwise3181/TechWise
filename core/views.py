from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string, get_template
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
import json
import io
import random
from django.utils import timezone
from datetime import timedelta
from .models import ServiceRequest, LaptopSale, LaptopRental, Laptop, OTPVerification, CartItem
from .forms import RegistrationForm, OTPForm

def home(request):
    # Fetch latest 6 laptops for featured section
    featured_laptops = Laptop.objects.all().order_by('-created_at')[:6]
    return render(request, 'core/index.html', {'featured_laptops': featured_laptops})

def buy(request):
    laptops = Laptop.objects.filter(availability_type__in=['Sale', 'Both'])
    return render(request, 'core/buy.html', {'laptops': laptops})

def rent(request):
    laptops = Laptop.objects.filter(availability_type__in=['Rent', 'Both'])
    return render(request, 'core/rent.html', {'laptops': laptops})

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Professional HTML Email Sending
        admin_email = 'techwise3181@gmail.com'
        subject_line = f"CONTACT FORM: {subject}"
        
        # Context for the template
        context = {
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
        }
        
        # Render HTML and Text versions
        html_content = render_to_string('core/emails/contact_email.html', context)
        text_content = f"New Contact Form Submission\n\nName: {name}\nEmail: {email}\nSubject: {subject}\n\nMessage:\n{message}"
        
        try:
            msg = EmailMultiAlternatives(
                subject_line,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [admin_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            
            messages.success(request, 'Thank you! Your message has been sent.')
        except Exception as e:
            print(f"EMAIL ERROR: {e}")
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            
        return redirect('contact')
        
    return render(request, 'core/contact.html')


def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            identifier = data.get('email') # This can now be username or email
            password = data.get('password')
            
            # 1. Try Username login
            user = authenticate(username=identifier, password=password)
            
            # 2. If fails, try Email login
            if user is None:
                try:
                    user_obj = User.objects.get(email=identifier)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is not None:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'user': {
                        'name': user.first_name or user.username,
                        'email': user.email,
                        'isLoggedIn': True,
                        'isSuperuser': user.is_superuser
                    }
                })
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return render(request, 'core/login.html')

def send_otp_email(request, email, otp_code, full_name):
    """
    Sends a professional HTML OTP email. No more debug fallback.
    """
    subject = f"Your TECHWISE Verification Code: {otp_code}"
    from_email = settings.DEFAULT_FROM_EMAIL
    
    # HTML Content
    html_content = render_to_string('core/emails/otp_email.html', {
        'otp': otp_code,
        'full_name': full_name
    })
    text_content = strip_tags(html_content) # Fallback for text-only clients

    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        # Log the error (optional, since this is localhost we can print)
        print(f"CRITICAL SMTP ERROR: {e}")
        # NO debug fallback here. We return False so the view can handle the error.
        return False

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            
            # Check if user or username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'This username is already taken.')
                return render(request, 'core/register.html', {'form': form})
                
            if User.objects.filter(email=email).exists():
                messages.error(request, 'This email is already registered. Please login.')
                return render(request, 'core/register.html', {'form': form})
            
            # Generate 6-digit OTP
            otp_code = f"{random.randint(100000, 999999)}"
            
            # Save/Update OTP record
            otp_record, _ = OTPVerification.objects.get_or_create(email=email)
            otp_record.otp = otp_code
            otp_record.created_at = timezone.now()
            otp_record.attempts = 0 # Reset attempts on new request
            otp_record.save()
            
            # Temporarily store registration data in session
            request.session['registration_data'] = {
                'full_name': form.cleaned_data['full_name'],
                'username': username,
                'email': email,
                'password': form.cleaned_data['password'] # Passwords are hashed by create_user later
            }
            
            # Send Email
            if send_otp_email(request, email, otp_code, form.cleaned_data['full_name']):
                messages.success(request, f'Verification code sent to {email}')
                return redirect('verify_otp')
            else:
                messages.error(request, 'Failed to send verification email. Please check SMTP settings.')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def verify_otp(request):
    reg_data = request.session.get('registration_data')
    if not reg_data:
        messages.warning(request, 'Session expired. Please register again.')
        return redirect('register')
    
    email = reg_data['email']
    
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            otp_record = OTPVerification.objects.filter(email=email).first()
            
            if not otp_record:
                messages.error(request, 'No active verification found. Please register.')
                return redirect('register')
            
            # 1. Check Expiry (5 minutes)
            if otp_record.created_at < timezone.now() - timedelta(minutes=5):
                messages.error(request, 'OTP has expired. Please resend a new code.')
            
            # 2. Check Attempts (Max 3)
            elif otp_record.attempts >= 3:
                messages.error(request, 'Too many failed attempts. This code is now invalid. Please resend.')
            
            # 3. Check Match
            elif otp_record.otp == otp_entered:
                # Success! Create the user account
                user = User.objects.create_user(
                    username=reg_data['username'],
                    email=email,
                    password=reg_data['password']
                )
                user.first_name = reg_data['full_name']
                user.save()
                login(request, user)
                
                # Cleanup
                otp_record.delete()
                del request.session['registration_data']
                
                messages.success(request, f'Registration successful! Welcome, {user.first_name}.')
                return redirect('home')
            
            else:
                # Incorrect OTP
                otp_record.attempts += 1
                otp_record.save()
                remaining = 3 - otp_record.attempts
                if remaining > 0:
                    messages.error(request, f'Invalid code. You have {remaining} attempts left.')
                else:
                    messages.error(request, 'Too many failed attempts. Please request a new code.')
    else:
        form = OTPForm()
    
    return render(request, 'core/verify_otp.html', {
        'form': form, 
        'email': email,
        'cooldown': 60 # Seconds for resend cooldown
    })

def resend_otp(request):
    reg_data = request.session.get('registration_data')
    if not reg_data:
        return redirect('register')
    
    email = reg_data['email']
    otp_record = OTPVerification.objects.filter(email=email).first()
    
    if otp_record:
        # Check Cooldown (60 seconds)
        time_elapsed = (timezone.now() - otp_record.updated_at).total_seconds()
        if time_elapsed < 60:
            messages.warning(request, f'Please wait {int(60 - time_elapsed)} seconds before resending.')
            return redirect('verify_otp')
    
    # Generate new code
    otp_code = f"{random.randint(100000, 999999)}"
    
    # Update Record
    if not otp_record:
        otp_record = OTPVerification(email=email)
    
    otp_record.otp = otp_code
    otp_record.created_at = timezone.now()
    otp_record.attempts = 0 # Reset attempts
    otp_record.save() # This updates updated_at automatically
    
    if send_otp_email(request, email, otp_code, reg_data['full_name']):
        messages.success(request, 'A new verification code has been sent.')
    else:
        messages.error(request, 'Failed to resend email.')
        
    return redirect('verify_otp')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    sales = LaptopSale.objects.filter(user=request.user).order_by('-sale_date')
    rentals = LaptopRental.objects.filter(user=request.user).order_by('-rental_date')
    services = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'core/dashboard.html', {
        'sales': sales,
        'rentals': rentals,
        'services': services
    })

def invoice(request, type, id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    order = None
    try:
        if type == 'sale':
            if request.user.is_superuser:
                order = LaptopSale.objects.get(id=id)
            else:
                order = LaptopSale.objects.get(id=id, user=request.user)
            order.invoice_date = order.sale_date
            order.unit_price = order.price
        elif type == 'rental':
            if request.user.is_superuser:
                order = LaptopRental.objects.get(id=id)
            else:
                order = LaptopRental.objects.get(id=id, user=request.user)
            order.invoice_date = order.rental_date
            order.unit_price = order.rental_price
    except (LaptopSale.DoesNotExist, LaptopRental.DoesNotExist):
        return redirect('dashboard' if not request.user.is_superuser else 'admin_dashboard')
    
    if order and order.laptop_specs:
        order.specs_list = [s.strip() for s in order.laptop_specs.split(',')]
    
    if not order:
        return redirect('dashboard')
    
    # Calculate order sequence for this specific user
    user_sales = LaptopSale.objects.filter(user=order.user, sale_date__lte=order.invoice_date).count()
    user_rentals = LaptopRental.objects.filter(user=order.user, rental_date__lte=order.invoice_date).count()
    order_sequence = user_sales + user_rentals
        
    return render(request, 'core/invoice.html', {
        'order': order, 
        'type': type, 
        'order_sequence': order_sequence
    })

def checkout(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Please login first'}, status=401)
            
        try:
            data = json.loads(request.body)
            laptop_id = data.get('laptop_id')
            laptop_name = data.get('laptop_name') or data.get('laptopModel')
            laptop_specs = data.get('laptop_specs') or data.get('laptopSpecs')
            qty = int(data.get('quantity', 1))
            mobile = data.get('mobile')
            
            # Fetch User's Cart
            cart_items = CartItem.objects.filter(user=request.user)
            
            if not cart_items.exists():
                return JsonResponse({'status': 'error', 'message': 'Your cart is empty.'}, status=400)
            
            # Validation
            if not mobile.replace('+', '').replace(' ', '').isdigit() or len(mobile.replace('+', '').replace(' ', '')) < 10:
                return JsonResponse({'status': 'error', 'message': 'Please enter a valid 10-digit mobile number.'}, status=400)

            orders_created = []

            for item in cart_items:
                # Calculate metrics
                tax_amount = (item.total_price * 12) / 100
                total_amount = item.total_price + tax_amount
                
                if item.transaction_type == 'sale':
                    order = LaptopSale.objects.create(
                        user=request.user,
                        laptop_name=item.laptop.name,
                        laptop_specs=item.laptop.specs,
                        price=item.laptop.price,
                        tax_amount=tax_amount,
                        total_amount=total_amount,
                        quantity=item.quantity,
                        customer_name=data.get('customerName'),
                        email=data.get('email'),
                        mobile_number=mobile,
                        address=data.get('address'),
                        pincode=data.get('pincode'),
                        state=data.get('state'),
                        district=data.get('district')
                    )
                    order_type = 'sale'
                else:
                    order = LaptopRental.objects.create(
                        user=request.user,
                        laptop_name=item.laptop.name,
                        laptop_specs=item.laptop.specs,
                        rental_price=item.laptop.rent_price,
                        tax_amount=tax_amount,
                        total_amount=total_amount,
                        quantity=item.quantity,
                        duration="30 days", # Default for now
                        customer_name=data.get('customerName'),
                        email=data.get('email'),
                        mobile_number=mobile,
                        address=data.get('address'),
                        pincode=data.get('pincode'),
                        state=data.get('state'),
                        district=data.get('district')
                    )
                    order_type = 'rental'
                
                # Decrement Stock
                item.laptop.stock -= item.quantity
                item.laptop.save()
                
                # Send Automated Invoice Email
                send_invoice_email(order, order_type)
                orders_created.append({'id': order.id, 'type': order_type})

            # Clear Cart
            cart_items.delete()
                
            return JsonResponse({
                'status': 'success', 
                'message': f'{len(orders_created)} orders placed successfully!',
                'redirect': '/dashboard/' 
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price for item in cart_items)
    return render(request, 'core/checkout.html', {'cart_items': cart_items, 'total': total})

@login_required
def order_success(request, type, id):
    order = None
    try:
        if type == 'sale':
            order = LaptopSale.objects.get(id=id, user=request.user)
        elif type == 'rental':
            order = LaptopRental.objects.get(id=id, user=request.user)
    except (LaptopSale.DoesNotExist, LaptopRental.DoesNotExist):
        return redirect('dashboard')
        
    if not order:
        return redirect('dashboard')
        
    return render(request, 'core/order_success.html', {'order': order, 'type': type})

def service_request(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Please login first'}, status=401)
            
        try:
            data = json.loads(request.body)
            ServiceRequest.objects.create(
                user=request.user,
                customer_name=data.get('name'),
                email=data.get('email'),
                mobile_number=data.get('mobile'),
                laptop_model=data.get('model', 'Unknown'),
                problem_type=data.get('type'),
                problem_description=data.get('description'),
                photos=data.get('photos', []),
                address=data.get('address'),
                pincode=data.get('pincode'),
                state=data.get('state'),
                district=data.get('district')
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return render(request, 'core/service_request.html')


def admin_dashboard(request):
    sales = LaptopSale.objects.all().order_by('-sale_date')
    rentals = LaptopRental.objects.all().order_by('-rental_date')
    services = ServiceRequest.objects.all().order_by('-created_at')
    laptops = Laptop.objects.all().order_by('-created_at')
    users = User.objects.all().order_by('-date_joined')
    
    return render(request, 'core/admin_dashboard.html', {
        'sales': sales,
        'rentals': rentals,
        'services': services,
        'laptops': laptops,
        'users': users
    })

@csrf_exempt
@login_required(login_url='admin_login')
def api_delete_record(request, type, id):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Admin access required'}, status=403)
    if request.method == 'POST':
        try:
            if type == 'sale':
                LaptopSale.objects.get(id=id).delete()
            elif type == 'rental':
                LaptopRental.objects.get(id=id).delete()
            elif type == 'service':
                ServiceRequest.objects.get(id=id).delete()
            elif type == 'laptop':
                Laptop.objects.get(id=id).delete()
            elif type == 'user':
                user_to_delete = User.objects.get(id=id)
                if user_to_delete.is_superuser:
                    return JsonResponse({'status': 'error', 'message': 'Cannot delete superusers'}, status=403)
                user_to_delete.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required(login_url='admin_login')
def api_manage_laptop(request):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Admin access required'}, status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            laptop_id = data.get('id')
            
            laptop_data = {
                'name': data.get('name'),
                'brand': data.get('brand'),
                'specs': data.get('specs'),
                'price': float(str(data.get('price')).replace('$', '').replace(',', '')),
                'rent_price': float(str(data.get('rent_price')).replace('$', '').replace(',', '')),
                'stock': int(data.get('stock', 0)),
                'image_url': data.get('image_url'),
                'availability_type': data.get('availability_type')
            }
            
            if laptop_id:
                Laptop.objects.filter(id=laptop_id).update(**laptop_data)
            else:
                Laptop.objects.create(**laptop_data)
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def user_activity(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')
        
    user = get_object_or_404(User, id=user_id)
    sales = LaptopSale.objects.filter(user=user).order_by('-sale_date')
    rentals = LaptopRental.objects.filter(user=user).order_by('-rental_date')
    services = ServiceRequest.objects.filter(user=user).order_by('-created_at')
    
    return render(request, 'core/user_activity.html', {
        'target_user': user,
        'sales': sales,
        'rentals': rentals,
        'services': services
    })

def admin_login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username_or_email = data.get('username')
            password = data.get('password')
            
            # Search by username or email
            user = authenticate(username=username_or_email, password=password)
            if user is None:
                # Try email fallback if username check failed
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None and user.is_superuser:
                logout(request) # Clear any existing user session
                login(request, user)
                return JsonResponse({'status': 'success'})
            elif user is not None:
                return JsonResponse({'status': 'error', 'message': 'Access denied: Superuser only'}, status=403)
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return render(request, 'core/admin_login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def send_invoice_email(order, order_type):
    """
    Generates a PDF invoice and sends it to the customer via email.
    """
    subject = f"Your TechWise Invoice: TW-{timezone.now().year}-{order.id:05d}"
    
    # Prepare context for PDF
    if order.laptop_specs:
        order.specs_list = [s.strip() for s in order.laptop_specs.split(',')]
    
    order.invoice_date = order.sale_date if order_type == 'sale' else order.rental_date
    
    context = {
        'order': order,
        'type': order_type,
    }
    
    # Generate PDF
    pdf_content = render_to_pdf('core/invoice_pdf.html', context)
    
    if pdf_content:
        # Prepare Email
        mail_subject = f"Invoice for your TechWise {order_type.capitalize()}: {order.laptop_name}"
        html_content = render_to_string('core/emails/invoice_email.html', {
            'order': order,
            'type': order_type
        })
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            mail_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [order.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.attach(f"Invoice_{order.id}.pdf", pdf_content, 'application/pdf')
        
        try:
            email.send(fail_silently=False)
            return True
        except Exception as e:
            print(f"Error sending invoice email: {e}")
            return False
    return False

@login_required
def download_invoice(request, type, id):
    order = None
    try:
        if type == 'sale':
            if request.user.is_superuser:
                order = LaptopSale.objects.get(id=id)
            else:
                order = LaptopSale.objects.get(id=id, user=request.user)
            order.invoice_date = order.sale_date
        elif type == 'rental':
            if request.user.is_superuser:
                order = LaptopRental.objects.get(id=id)
            else:
                order = LaptopRental.objects.get(id=id, user=request.user)
            order.invoice_date = order.rental_date
    except (LaptopSale.DoesNotExist, LaptopRental.DoesNotExist):
        return HttpResponse("Order not found.", status=404)

    if not order:
        return HttpResponse("Order not found.", status=404)

    if order.laptop_specs:
        order.specs_list = [s.strip() for s in order.laptop_specs.split(',')]
    
    context = {
        'order': order,
        'type': type,
        'request': request
    }
    
    pdf = render_to_pdf('core/invoice_pdf.html', context)
    if pdf:
        filename = f"Invoice_{order.id}.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=500)

@login_required
def track_order(request, type, id):
    order = None
    try:
        if type == 'sale':
            if request.user.is_superuser:
                order = LaptopSale.objects.get(id=id)
            else:
                order = LaptopSale.objects.get(id=id, user=request.user)
        elif type == 'rental':
            if request.user.is_superuser:
                order = LaptopRental.objects.get(id=id)
            else:
                order = LaptopRental.objects.get(id=id, user=request.user)
    except (LaptopSale.DoesNotExist, LaptopRental.DoesNotExist):
        return redirect('dashboard')
        
    if not order:
        return redirect('dashboard')
    
    # Check if order hasn't been shipped yet (default lat/lng)
    start_lat = order.current_lat if order.current_lat else 11.2588  # Default Calicut/Vadakara approx
    start_lng = order.current_lng if order.current_lng else 75.7804  # Default Calicut/Vadakara approx

    return render(request, 'core/tracking.html', {
        'order': order,
        'type': type,
        'start_lat': start_lat,
        'start_lng': start_lng
    })

@csrf_exempt
@login_required(login_url='admin_login')
def api_update_tracking(request):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Admin access required'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_type = data.get('type')
            order_id = data.get('id')
            status = data.get('status')
            lat = data.get('lat')
            lng = data.get('lng')
            est_delivery = data.get('estimated_delivery')

            order = None
            if order_type == 'sale':
                order = LaptopSale.objects.get(id=order_id)
            elif order_type == 'rental':
                order = LaptopRental.objects.get(id=order_id)
            
            if order:
                if status: order.status = status
                if lat: order.current_lat = float(lat)
                if lng: order.current_lng = float(lng)
                if est_delivery: order.estimated_delivery = est_delivery
                order.save()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def add_to_cart(request, laptop_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            laptop = get_object_or_404(Laptop, id=laptop_id)
            qty = int(data.get('quantity', 1))
            t_type = data.get('type', 'sale') # 'sale' or 'rental'
            
            # Check stock
            if laptop.stock < qty:
                return JsonResponse({'status': 'error', 'message': f'Only {laptop.stock} units available.'}, status=400)
                
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                laptop=laptop,
                transaction_type=t_type,
                defaults={'quantity': qty}
            )
            
            if not created:
                cart_item.quantity += qty
                cart_item.save()
                
            return JsonResponse({'status': 'success', 'message': f'{laptop.name} added to cart.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price for item in cart_items)
    return render(request, 'core/cart.html', {'cart_items': cart_items, 'total': total})

@csrf_exempt
@login_required
def remove_from_cart(request, item_id):
    if request.method == 'DELETE':
        CartItem.objects.filter(id=item_id, user=request.user).delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
@login_required
def update_cart_qty(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_qty = int(data.get('quantity'))
            item = get_object_or_404(CartItem, id=item_id, user=request.user)
            
            if item.laptop.stock < new_qty:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Sorry, only {item.laptop.stock} units available.'
                }, status=400)
                
            item.quantity = new_qty
            item.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def cancel_order(request, type, id):
    order = None
    try:
        if type == 'sale':
            order = LaptopSale.objects.get(id=id, user=request.user)
        elif type == 'rental':
            order = LaptopRental.objects.get(id=id, user=request.user)
            
        if order and order.status in ['Order Placed', 'Order Confirmed']:
            # 1. Restore Stock
            try:
                laptop = Laptop.objects.filter(name=order.laptop_name).first()
                if laptop:
                    laptop.stock += order.quantity
                    laptop.save()
            except Exception as stock_err:
                print(f"Stock restoration error: {stock_err}")

            # 2. Update Status
            order.status = 'Cancelled'
            order.save()
            messages.success(request, f'Order for {order.laptop_name} has been cancelled and stock restored.')
        else:
            messages.error(request, 'Order cannot be cancelled at this stage.')
            
    except Exception as e:
        messages.error(request, f'Error cancelling order: {e}')
        
    return redirect('dashboard')
