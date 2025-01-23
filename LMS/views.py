from django.shortcuts import redirect, render
from app.models import Categories, Course, Level, Video, UserCourse, Payment, LearningResource
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib import messages
from app.templatetags.course_tags import discount_calculation
from django.contrib.auth.models import User

from django.views.decorators.csrf import csrf_exempt
from .settings import KEY_ID, KYE_SECRET
from time import time
import razorpay
client = razorpay.Client(auth=(KEY_ID,KYE_SECRET))

# ------------------------------------------------
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel
import difflib
from django.shortcuts import render
from django.http import JsonResponse
from app.filters import LearningResourceFilter
from django.core.paginator import Paginator

# ------------------------------------------------


def create_sim(search):
    df_org = pd.read_csv('coursera_courses.csv')
    df = df_org.copy()
    df.drop(['course_organization', 'course_certificate_type', 'course_time', 'course_rating', 'course_reviews_num', 'course_difficulty', 'course_url', 'course_students_enrolled', 'course_summary', 'course_description'], axis=1, inplace=True)

    tfv = TfidfVectorizer(min_df=3, max_features=None, 
            strip_accents='unicode', analyzer='word', token_pattern=r'\w{1,}',
            ngram_range=(1, 3),
            stop_words='english')

    df['cleaned'] = df['course_skills'].fillna('')
    tfv_matrix = tfv.fit_transform(df['cleaned'])
    sig = sigmoid_kernel(tfv_matrix, tfv_matrix)
    indices = pd.Series(df.index, index=df['course_title']).drop_duplicates()

    def give_rec(title, sig=sig):
        idx = indices[title]
        sig_scores = list(enumerate(sig[idx]))
        sig_scores = sorted(sig_scores, key=lambda x: x[1], reverse=True)
        sig_scores = sig_scores[1:21]
        course_indices = [i[0] for i in sig_scores]

        # Select specific columns for output
        selected_columns = ['course_title', 'course_organization', 'course_time', 'course_rating', 'course_url', 'course_students_enrolled', 'course_summary', 'course_description']
        return df_org.loc[course_indices, selected_columns]

    namelist = df['course_title'].tolist()
    word = search
    simlist = difflib.get_close_matches(word, namelist)
    try: 
        findf = give_rec(simlist[0])
        findf = findf.reset_index(drop=True)
    except:
        findf = pd.DataFrame()

    return findf

def recommendations(request):
    category = Categories.objects.all().order_by('id')[0:10]
    resource = LearningResource.objects.all()
    search_filter = LearningResourceFilter(request.GET, queryset=resource)
    filtered_resources = search_filter.qs
    resource = filtered_resources.order_by('course_title')

    # Handle the search query for recommendations
    search_query = request.GET.get('course_title')
    if search_query:
        recommendation_df = create_sim(search_query)
        if not recommendation_df.empty:
            # Assuming you want to use the recommendations in the context
            context = {
                "category": category,
                "resource": recommendation_df.to_dict(orient='records'),  # Convert to a list of dicts for easy use in the template
                "search_filter": search_filter,
                "page_obj": None,  # No pagination for recommendations
            }
        else:
            context = {
                "category": category,
                "resource": None,
                "search_filter": search_filter,
                "page_obj": None,
                "message": "Sorry! We did not find any matching courses. Try adding more keywords in your search."
            }
        return render(request, 'search/recommendations.html', context)

    # Pagination for normal search results
    paginator = Paginator(resource, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "category": category,
        "resource": resource,
        "search_filter": search_filter,
        "page_obj": page_obj
    }
    
    return render(request, 'search/recommendations.html', context)



# ------------------------------------------------

def BASE(request):
    return render(request, 'base.html')

def PAGE_NOT_FOUND(request):
    category = Categories.objects.all().order_by('id')[0:10]
    context = {
        'category': category,
    }
    return render(request, 'error/404.html', context)

def HOME(request):
    category = Categories.objects.all().order_by('id')[0:10]
    course = Course.objects.filter(status = 'PUBLISH').order_by('-id')
    
    context = {
        'category': category,
        'course': course,
    }
    return render(request, 'Main/home.html', context)

def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price = 0).count()
    PaidCourse_count = Course.objects.filter(price__gte = 1).count()

    context = {
        'category': category,
        'level': level,
        'course': course,
        'FreeCourse_count':FreeCourse_count,
        'PaidCourse_count':PaidCourse_count,
    }
    return render(request, 'Main/single_course.html', context)

def filter_data(request):
    categories = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')
    
    if price == ['PriceAll']:
        course = Course.objects.all()
    elif price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif categories:
        course = Course.objects.filter(category__id__in = categories).order_by('-id')
    elif level:
        course = Course.objects.filter(level__id__in=level).order_by('-id')
    else:
        course = Course.objects.all().order_by('-id')

    context = {
        'course':course
    }
    t = render_to_string('ajax/course.html', context)
    return JsonResponse({'data': t})


def SEARCH_COURSE(request):
    category = Categories.objects.all().order_by('id')[0:10]
    query = request.GET['query']
    course = Course.objects.filter(title__icontains=query)
    # print('------------------')
    # print(query)
    # print(course)
    # print('------------------')
    context = {
        'course': course,
        'category': category,
    }
    return render(request, 'search/search.html', context)

def COURSE_DETAILS(request, slug):
    category = Categories.objects.all().order_by('id')[0:10]
    time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))
    course = Course.objects.filter(slug=slug)
    course_id = Course.objects.get(slug=slug)
    
    try:
        check_enroll = UserCourse.objects.get(user= request.user, course = course_id)
    except UserCourse.DoesNotExist:
        check_enroll = None
    if course.exists():
        course = course.first
    else:
        return redirect('404')
    
    context = {
        'category': category,
        'course': course,
        'time_duration': time_duration,
        'check_enroll': check_enroll,
    }
    return render(request, 'course/course_details.html', context)


def COURSE_DETAILS(request, slug):
    # Ensure the user is authenticated
    if request.user.is_authenticated:
        category = Categories.objects.all().order_by('id')[0:10]
        
        # Ensure the course exists and get the first instance
        course = Course.objects.filter(slug=slug).first()
        if not course:
            return redirect('404')  # Assuming '404' is your 404 error view
        
        time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))
        
        # Get the course_id explicitly from the course object
        course_id = course.id
        
        # Attempt to get the UserCourse object, handling the case where it might not exist
        try:
            check_enroll = UserCourse.objects.get(user=request.user, course_id=course_id)
        except UserCourse.DoesNotExist:
            check_enroll = None
        
        context = {
            'category': category,
            'course': course,
            'time_duration': time_duration,
            'check_enroll': check_enroll,
        }
        return render(request, 'course/course_details.html', context)
    
    else:
        # User is not authenticated, but still render the page
        category = Categories.objects.all().order_by('id')[0:10]
        
        # Ensure the course exists and get the first instance
        course = Course.objects.filter(slug=slug).first()
        if not course:
            return redirect('404')  # Assuming '404' is your 404 error view
        
        time_duration = Video.objects.filter(course__slug=slug).aggregate(sum=Sum('time_duration'))
        
        context = {
            'category': category,
            'course': course,
            'time_duration': time_duration,
            'check_enroll': None,  # User is not authenticated, so no enrollment check needed
        }
        return render(request, 'course/course_details.html', context)


def WATCH_COURSE(request, slug):
    course = Course.objects.filter(slug=slug)
    lecture = request.GET.get('lecture')
    course_id = Course.objects.get(slug=slug)

    try:
        # check_enroll = UserCourse.objects.get(user=request.user, course=course_id)
        video = Video.objects.get(id=lecture)
        if course.exists():
            course = course.first()
        else:
            return redirect('404')
    except UserCourse.DoesNotExist:
        return redirect('404')

    context = {
        'course': course,
        'video': video,
        'lecture': lecture,
    }
    return render(request, 'course/watch_course.html', context)
    



def CONTACT_US(request):
    category = Categories.objects.all().order_by('id')[0:10]
    context = {
        'category': category,
    }
    return render(request, 'Main/contact_us.html', context)

def ABOUT_US(request):
    category = Categories.objects.all().order_by('id')[0:10]
    context = {
        'category': category,
    }
    return render(request, 'Main/about_us.html', context)

def CHECKOUT(request, slug):
    category = Categories.objects.all().order_by('id')[0:10]
    course = Course.objects.get(slug = slug)
    action = request.GET.get('action')
    order = None
    
    if request.user.is_authenticated:
        if course.discount == 100:
            course = UserCourse(
                user = request.user,
                course = course,
            )
            course.save()
            messages.success(request, 'Course Enrolled Successfully!!')
            return redirect('my_course')
        # elif action == 'create_payment' :
        #     if course.discount <= 0:
        #         course = UserCourse(
        #             user = request.user,
        #             course = course,
        #         )
        #         course.save()
        #         messages.success(request, 'Course Enrolled Successfully!!')
        #         return redirect('my_course')
            
        elif action == 'create_payment' :
            if request.method == 'POST':
                first_name = request.POST.get('billing_first_name')
                last_name = request.POST.get('billing_last_name')
                country = request.POST.get('billing_country')
                address_1 = request.POST.get('billing_address_1')
                address_2 = request.POST.get('billing_address_2')
                city = request.POST.get('billing_city')
                state = request.POST.get('billing_state')
                postcode = request.POST.get('billing_postcode')
                phone = request.POST.get('billing_phone')
                email = request.POST.get('billing_email')
                order_comments = request.POST.get('order_comments')

                # amount = course.price * 100
                amount = discount_calculation(course.price, course.discount) * 100
                currency = "INR"
                notes = {
                    "name": f'{first_name} {last_name}',
                    "country": country,
                    "address":f'{address_1} {address_2}',
                    "city":city,
                    "state":state,
                    "postcode":postcode,
                    "phone":phone,
                    "email":email,
                    "order_comments":order_comments,
                }
                receipt = f'NumiTech-{int(time())}'
                order = client.order.create(
                    {
                        'receipt': receipt,
                        'notes': notes,
                        'amount': amount,
                        'currency': currency,
                        
                    }
                )
                
                payment = Payment(
                    course = course,
                    user = request.user,
                    order_id = order.get('id')
                )
                payment.save()
        context = {
            'course': course,
            'order': order,
            'category': category,
            }
        return render(request, 'checkout/checkout.html', context)
    else:
        messages.warning(request, 'You need to login first')
        return redirect('login')

@csrf_exempt
def VERIFY_PAYMENT(request):
    category = Categories.objects.all().order_by('id')[0:10]
    if request.method == 'POST':
        data = request.POST 
        try:
            client.utility.verify_payment_signature(data)
            razorpay_order_id = data['razorpay_order_id']
            razorpay_payment_id = data['razorpay_payment_id']
            
            payment = Payment.objects.get(order_id = razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True
            
            usercourse = UserCourse(
                user = payment.user,
                course = payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()
            
            context = {
                'data': data,
                'payment': payment,
                'category': category,
            }
            return render(request, 'verify_payment/success.html', context)
        except:
            context = {
                'category': category,
            }
            return render(request, 'verify_payment/fail.html', context)


def MY_COURSE(request):
    category = Categories.objects.all().order_by('id')[0:10]
    course = UserCourse.objects.filter(user = request.user)
    # time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))
    
    context = {
        'course': course,
        # 'time_duration': time_duration,
        'category': category,
    }
    return render(request, 'course/my_course.html', context)
