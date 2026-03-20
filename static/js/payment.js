// Payment Gateway - Disabled (Page-based flow)
console.log('Payment modal disabled - using dedicated payment page');


function openPaymentModal() {
    // Extract order data from hidden inputs
    orderData = {
        productId: document.getElementById('data-product-id')?.value || document.querySelector('input[name="product_id"]')?.value || 'cart',
        isCart: document.getElementById('data-is-cart')?.value === 'true' || false,
        quantity: parseInt(document.getElementById('data-quantity')?.value || document.querySelector('input[name="quantity"]')?.value || 1),
        totalAmount: parseFloat(document.getElementById('data-total')?.value || document.querySelector('.total')?.textContent.replace(/[^0-9.]/g, '') || 0),
        productName: document.getElementById('data-product-name')?.value || document.querySelector('h2')?.textContent.trim() || 'Order Items',
        image: document.getElementById('data-image')?.value || document.querySelector('img')?.src || ''
    };
    
    // Populate order summary
    const summaryEl = document.getElementById('order-summary');
    if (orderData.isCart) {
        summaryEl.innerHTML = `<strong>🛒 Cart Checkout - Total: ₹${orderData.totalAmount.toFixed(2)}</strong>`;
    } else {
        summaryEl.innerHTML = `
            <img src="${orderData.image}" alt="${orderData.productName}" style="width:60px;height:60px;border-radius:8px">
            <div style="flex:1">
                <div style="font-weight:600;font-size:14px">${orderData.productName}</div>
                <div style="color:#666;font-size:12px">Qty: ${orderData.quantity} × ₹${Math.round(orderData.totalAmount/orderData.quantity)} = ₹${orderData.totalAmount.toFixed(2)}</div>
            </div>
        `;
    }
    
    // Reset tabs and forms
    switchTab('upi');
    document.querySelectorAll('.payment-form input, .payment-form select').forEach(field => field.value = '');
    
    document.getElementById('payment-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closePaymentModal() {
    document.getElementById('payment-modal').style.display = 'none';
    document.body.style.overflow = '';
    document.querySelector('form.payment-form').reset();
}

function switchTab(tab) {
    currentTab = tab;
    // Animate out old tab
    document.querySelector('.tab-content.active')?.classList.add('fade-out');
    
    setTimeout(() => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        document.querySelectorAll('.tab-content').forEach(c => {
            c.classList.remove('active', 'fade-out', 'fade-in');
        });
        const newContent = document.getElementById(tab + '-content');
        newContent.classList.add('active', 'fade-in');
    }, 150);
}

function proceedPayment() {
    let paymentData;
    
    switch (currentTab) {
        case 'upi':
            const upiId = document.getElementById('upi-id').value.trim();
            if (!upiId || !upiId.includes('@')) {
                alert('Please enter valid UPI ID (e.g., name@paytm)');
                return;
            }
            paymentData = { method: 'UPI', upi_id: upiId };
            break;
        case 'card':
            const cardNum = document.getElementById('card-number').value.replace(/\\s/g, '');
            const name = document.getElementById('card-name').value;
            const expiry = document.getElementById('expiry').value;
            const cvv = document.getElementById('cvv').value;
            if (cardNum.length !== 16 || !name || !expiry || cvv.length !== 3) {
                alert('Please fill valid card details');
                return;
            }
            paymentData = { method: 'Card', card_number: cardNum, expiry, cvv, name };
            break;
        case 'netbanking':
            const bank = document.getElementById('bank').value;
            paymentData = { method: 'Net Banking', bank };
            break;
        case 'qr':
            paymentData = { method: 'QR Code' };
            break;
        default:
            alert('Please select a payment method');
            return;
    }
    
    // Show processing
    const btn = document.querySelector('.proceed-btn');
    btn.textContent = 'Processing...';
    btn.disabled = true;
    
    // AJAX POST
    const formData = new FormData();
    formData.append('payment_method', 'online');
    formData.append('quantity', orderData.quantity);
    formData.append('payment_details', JSON.stringify(paymentData));
    
    fetch(`/orders/review/${orderData.productId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.json().then(data => {
                if (data.success) showSuccess();
            });
        }
    })
    .catch(err => {
        console.error('Payment failed', err);
        alert('Payment processing failed. Please try again.');
        btn.textContent = 'Proceed Payment';
        btn.disabled = false;
    });
}

function showSuccess() {
    // Hide form, show success
    document.querySelector('.payment-content').style.display = 'none';
    document.getElementById('success-message').style.display = 'block';
    
    // Animate checkmark
    const check = document.getElementById('checkmark');
    check.style.opacity = '1';
    check.style.transform = 'scale(1)';
    
    // Confetti (simple CSS)
    document.body.classList.add('confetti');
    
    // Redirect after 2s
    setTimeout(() => {
        window.location.href = '/orders/my_orders';
    }, 2000);
}


