from backend.atomic.notification.notification import send_email_notification  # Import the send_email_notification function
# Function to check credit score and take actions
def check_credit_score_and_notify(user):
    # Retrieve the user's credit score and suspension status
    credit_score = user.get('credit_score')
    is_suspended = user.get('is_suspended')
    is_suspended = 'NO'
    email = user.get('email')
    
    # If credit score is lower than 50
    if credit_score < 50:
        # Change suspension status
        is_suspended = 'YES'
        
        # Send email about suspension
        send_email_notification(
            email, 
            'Suspension', 
            'You are suspended for a month due to frequent cancellations/bad conduct.'
        )
        
        # Set credit score to 50 after suspension
        credit_score = 50
    
    # If credit score is between 50 and 70
    elif credit_score < 70:
        # Send a warning about bad conduct
        send_email_notification(
            email, 
            'Warning', 
            'Warning of bad conduct.'
        )
    
    # If credit score is 70 or above, no action needed
    else:
        # No action required
        print(f"{user['name']} has a good credit score. No action required.")
    
    # Update user's suspension status if needed
    user['is_suspended'] = is_suspended
    # Update the user's credit score
    user['credit_score'] = credit_score
    
    return user


# Example usage
user = {
    'name': 'John Doe',
    'email': 'email',
    'credit_score': 49,  # Example: User with low credit score
    'is_suspended': 'YES'
}

# Check the credit score and perform actions
updated_user = check_credit_score_and_notify(user)

print(updated_user)  # Print the updated user data


