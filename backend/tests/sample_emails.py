"""
RETURNKART.IN — SAMPLE EMAILS FOR TESTING
Realistic fake order emails from top Indian ecommerce brands.
Use with POST /api/orders/test-parse to test the Gemini parser.
"""

SAMPLE_EMAILS = {
    "amazon": {
        "platform": "amazon",
        "email_text": """Subject: Your Amazon.in order #408-3956234-7821940 has been confirmed
From: auto-confirm@amazon.in
Date: Wed, 19 Mar 2026 10:30:00 +0530

Hello Priya,

Thank you for your order. We'll send a confirmation when your order ships.

Order #408-3956234-7821940
Placed on 19 March, 2026

Order Details:
Samsung Galaxy Buds FE (Graphite)
Qty: 1
Price: Rs. 4,999.00

Shipping Address:
42, MG Road, Koramangala
Bengaluru, Karnataka 560034

Estimated delivery: 22 March, 2026
Shipping by: Amazon Logistics

Payment: ICICI Bank Credit Card ending in 4521
Subtotal: Rs. 4,999.00
Shipping: FREE
Total: Rs. 4,999.00

Return Policy: 10-day replacement only for electronics

Thank you for shopping with us.
Amazon.in"""
    },

    "flipkart": {
        "platform": "flipkart",
        "email_text": """Subject: Your Flipkart order OD4285167293847561 is confirmed!
From: noreply@flipkart.com
Date: Tue, 18 Mar 2026 14:20:00 +0530

Hi Rahul,

Your order has been confirmed and is being processed.

Order ID: OD4285167293847561
Order Date: 18 March 2026

Items in your order:
1. Nike Air Force 1 '07 - White/White (Size: UK 9)
   Seller: RetailNet
   Price: Rs 7,495

Delivery Address:
15, Sector 62, Noida
Uttar Pradesh - 201301

Expected Delivery: 21 March, 2026
Shipped by: Ekart Logistics

Payment Method: Flipkart Pay Later
Item Total: Rs 7,495
Discount: -Rs 500
Delivery Charges: FREE
Total Amount: Rs 6,995

30-day return/exchange policy applies.

Happy Shopping!
Team Flipkart"""
    },

    "myntra": {
        "platform": "myntra",
        "email_text": """Subject: Order Confirmed! Your Myntra order MN92817364500 is on its way
From: noreply@myntra.com
Date: Mon, 17 Mar 2026 09:45:00 +0530

Hey Ananya!

Great choice! Your order has been confirmed.

Order Number: MN92817364500
Date: 17 March, 2026

Roadster Men Solid Denim Jacket - Blue
Size: M | Qty: 1
MRP: Rs 2,499
You Pay: Rs 1,899 (24% OFF)

Delivery to: Ananya Sharma
23, Banjara Hills, Hyderabad
Telangana - 500034

Expected by: 20 March, 2026

Payment: UPI (Google Pay)
Total Paid: Rs 1,899

30-day easy returns. No questions asked.

Love,
Team Myntra"""
    },

    "hm": {
        "platform": "hm",
        "email_text": """Subject: Your H&M receipt
From: in@delivery.hm.com
Date: Sat, 15 Mar 2026 18:00:00 +0530

Thank you for your purchase!

Order number: 5102938475
Date: 15 March 2026

Oversized Hoodie - Sage Green
Art. No. 1012345001
Size: L
Qty: 1
Rs. 1,999.00

Skinny Fit Jeans - Black
Art. No. 1098765002
Size: 32
Qty: 1
Rs. 1,499.00

Delivery address:
Flat 12B, Prestige Shantiniketan
Whitefield, Bangalore 560048

Subtotal: Rs. 3,498.00
Delivery: Free
Total: Rs. 3,498.00

Payment: Visa ending in 8832

Expected delivery: 19-22 March 2026

15-day return policy. Items must be unworn with tags attached.

Happy Shopping!
H&M India"""
    },

    "zara": {
        "platform": "zara",
        "email_text": """Subject: Order confirmation #53104872956
From: info@zara.com
Date: Sun, 16 Mar 2026 11:30:00 +0530

Dear Customer,

Your ZARA order has been received.

Order: 53104872956
Date: 16/03/2026

TEXTURED SUIT BLAZER - NAVY BLUE
Ref: 1564/320/401
Size: M (EUR 40)
Qty: 1
Rs. 5,990.00

SLIM FIT TROUSERS - NAVY
Ref: 7385/320/401  
Size: 32
Qty: 1
Rs. 2,990.00

Ship to:
45 Linking Road, Bandra West
Mumbai, Maharashtra 400050

Subtotal: Rs. 8,980.00
Shipping: Free
Total: Rs. 8,980.00

Paid with: Mastercard ****6729

Estimated delivery: 20-23 March 2026
Carrier: Blue Dart

You have 30 days from the shipping date to return.

ZARA India"""
    },

    "meesho": {
        "platform": "meesho",
        "email_text": """Subject: Your Meesho order is placed! Order #MS8847291034
From: noreply@meesho.com
Date: Wed, 19 Mar 2026 16:10:00 +0530

Hi Deepa,

Your order has been placed successfully!

Order ID: MS8847291034
Placed on: 19 March, 2026

Product: Women Rayon Anarkali Kurti Set - Maroon
Size: XL | Qty: 1
Price: Rs 699

Delivery Address:
78, Gandhi Nagar
Jaipur, Rajasthan 302015

Estimated Delivery: 24-26 March 2026
Shipping partner: Valmo Logistics

Payment: Cash on Delivery
Total: Rs 699 (Free Delivery)

7-day return window from delivery.

Thank you for shopping on Meesho!"""
    },

    "ajio": {
        "platform": "ajio",
        "email_text": """Subject: AJIO Order Confirmed - AJ029384756
From: noreply@ajio.com
Date: Thu, 13 Mar 2026 20:00:00 +0530

Hey Karthik,

Your AJIO order is confirmed!

Order #AJ029384756
Date: 13 March 2026

Puma RS-X Reinvention Sneakers - Puma Black
Size: UK 8 | Qty: 1
MRP: Rs 8,999
You Pay: Rs 6,499 (28% OFF)

Shipping to:
5th Cross, Indiranagar
Bengaluru, Karnataka 560038

Delivery by: 17 March 2026
Shipped via: AJIO Logistics

Paid with: Amazon Pay Balance
Order Total: Rs 6,499

30-day return and exchange policy.

Happy Shopping!
Team AJIO"""
    },

    "nykaa": {
        "platform": "nykaa",
        "email_text": """Subject: Your Nykaa Fashion order has been placed!
From: orders@nykaafashion.com
Date: Fri, 14 Mar 2026 13:15:00 +0530

Hi Shreya!

Thank you for your order.

Order Number: NKFA-2938475610
Date: 14 March 2026

Tommy Hilfiger Men Core 1985 Regular Polo - Desert Sky
Size: M | Qty: 1
MRP: Rs 5,499
Price: Rs 3,999

Delivery Address:
22, Aundh Road
Pune, Maharashtra 411007

Expected Delivery: 18-19 March 2026
Shipping: Delhivery

Payment: PhonePe UPI
Total: Rs 3,999

15-day easy returns.

XOXO,
Nykaa Fashion"""
    },

    "tommy_hilfiger": {
        "platform": "tommyhilfiger",
        "email_text": """Subject: Thank you for your purchase! Order #TH-IN-928374
From: noreply@e.tommy.in
Date: Mon, 17 Mar 2026 10:00:00 +0530

Dear Customer,

Thank you for shopping with Tommy Hilfiger India.

Order Number: TH-IN-928374
Order Date: 17 March 2026

Pure Cotton Flag Logo Oxford Shirt - Optic White
Size: M
Qty: 1
Rs 5,999.00

Tommy Jeans Slim Scanton Jeans - Aspen Dark Blue
Size: 32/32
Qty: 1
Rs 6,999.00

Shipping Address:
14A, Vasant Vihar
New Delhi 110057

Subtotal: Rs 12,998.00
Shipping: Free
Total: Rs 12,998.00

Paid by: HDFC Credit Card ending 3847

Estimated delivery: 22-25 March 2026

30-day return policy applies.

Best regards,
Tommy Hilfiger India"""
    },

    "nike": {
        "platform": "nike",
        "email_text": """Subject: We've got your order. Nike Order #C10293847
From: nike@info.nike.com
Date: Tue, 18 Mar 2026 11:45:00 +0530

Hi Arjun,

Your order is confirmed.

Order #C10293847
Order date: 18 March 2026

Nike Air Max 90 - White/Black
Size: UK 9
Qty: 1
MRP: Rs 11,895
Price: Rs 8,327 (30% off)

Ship to:
67, Park Street
Kolkata, West Bengal 700016

Estimated arrival: 23-25 March 2026

Payment: Nike Member Credit
Subtotal: Rs 8,327
Delivery: Free for Nike Members
Total: Rs 8,327

30-day return policy. Nike Members get free returns.

Just Do It.
Nike India"""
    },

    "levi_s": {
        "platform": "levis",
        "email_text": """Subject: Your Levi's order has been placed - #LV-IN-485739
From: noreply@email.levi.in
Date: Sun, 16 Mar 2026 15:30:00 +0530

Hey there!

Your order is confirmed.

Order Number: LV-IN-485739
Date: 16 March 2026

Levi's 501 Original Fit Jeans - Stonewash
Size: 32W x 32L
Qty: 1
MRP: Rs 4,599
Price: Rs 3,219 (30% OFF)

Ship to:
9, Anna Salai, T Nagar
Chennai, Tamil Nadu 600017

Estimated delivery: 20-22 March 2026

Payment: Axis Bank Debit Card
Total: Rs 3,219

30-day hassle-free returns.

Live in Levi's."""
    },

    "adidas": {
        "platform": "adidas",
        "email_text": """Subject: Order confirmed - adidas order AD384756IN
From: noreply@e.adidas.co.in
Date: Fri, 14 Mar 2026 09:00:00 +0530

Hi Vikram,

Thanks for your order!

Order number: AD384756IN
Date: 14 March 2026

adidas Ultraboost Light Running Shoes
Colour: Core Black / Cloud White
Size: UK 9
Qty: 1
MRP: Rs 16,999
You Pay: Rs 11,899 (30% off)

Delivery to:
34, FC Road
Pune, Maharashtra 411004

Expected delivery: 18-20 March 2026

Paid with: Paytm Wallet
Total: Rs 11,899

30-day return. Free returns for adiClub members.

adidas India"""
    },
}


def get_all_sample_names():
    return list(SAMPLE_EMAILS.keys())


def get_sample_email(name: str) -> dict:
    return SAMPLE_EMAILS.get(name)
