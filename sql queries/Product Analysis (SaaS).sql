-- =====================================================
-- PRODUCT ANALYTICS & USER GROWTH
-- =====================================================

-- PostgreSQL Table Creation
--------------------------------------------------------
-- 1. USERS
--------------------------------------------------------
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    signup_date DATE NOT NULL,
    country VARCHAR(50),
    age_group VARCHAR(20),
    gender VARCHAR(20),
    acquisition_channel VARCHAR(50),
    device_type VARCHAR(20),
    initial_plan VARCHAR(30),
    account_status VARCHAR(30)
);

-- 2. SESSIONS
--------------------------------------------------------
CREATE TABLE sessions (
    session_id VARCHAR(20) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    session_date DATE NOT NULL,
    session_start TIMESTAMP NOT NULL,
    session_duration_minutes INTEGER NOT NULL,
    pages_viewed INTEGER NOT NULL,
    device_type VARCHAR(20),
	CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. PRODUCT EVENTS
--------------------------------------------------------
CREATE TABLE product_events (
    event_id VARCHAR(20) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    session_id VARCHAR(20) NOT NULL,
    event_date DATE NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    event_name VARCHAR(50) NOT NULL,
    feature_name VARCHAR(50) NOT NULL,
    device_type VARCHAR(20),
    CONSTRAINT fk_events_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_events_session FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 4. SUBSCRIPTIONS
--------------------------------------------------------
CREATE TABLE subscriptions (
    subscription_id VARCHAR(20) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_type VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_price NUMERIC(10,2) NOT NULL,
    subscription_status VARCHAR(30),
    renewal_status VARCHAR(30),
	CONSTRAINT fk_subscriptions_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 5. TRANSACTIONS
--------------------------------------------------------
CREATE TABLE transactions (
    transaction_id VARCHAR(20) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    subscription_id VARCHAR(20) NOT NULL,
    transaction_date DATE NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    payment_method VARCHAR(30),
    transaction_type VARCHAR(30),
    transaction_status VARCHAR(30),
	CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES users(user_id),
	CONSTRAINT fk_transactions_subscription FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id)
);

-- 6. MARKETING CAMPAIGNS
--------------------------------------------------------
CREATE TABLE marketing_campaigns (
    campaign_id VARCHAR(20) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    campaign_date DATE NOT NULL,
    campaign_name VARCHAR(100),
    channel VARCHAR(50),
    impressions BIGINT NOT NULL,
    clicks BIGINT NOT NULL,
    spend NUMERIC(14,2) NOT NULL,
    conversion INTEGER NOT NULL,
    CONSTRAINT fk_marketing_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 7. SUPPORT TICKETS
--------------------------------------------------------
CREATE TABLE support_tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    created_date DATE NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20),
    resolution_time_hours NUMERIC(10,2),
    ticket_status VARCHAR(30),
    customer_rating NUMERIC(3,1),
    CONSTRAINT fk_support_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);


-- =====================================================
-- SQL Business Questions — 24
-- =====================================================

-- 1. User Growth & Acquisition — 4
--------------------------------------------------------
-- Q1. How many new users signed up each month ?
	SELECT
		DATE_TRUNC('month', signup_date)::date as months,
		COUNT(user_id) as new_users
	FROM users
	GROUP BY months
	ORDER BY months
	
-- Q2. Which acquisition channels bring the highest number of users?
	SELECT
		acquisition_channel,
		COUNT(user_id) as total_users
	FROM users
	GROUP BY acquisition_channel
	ORDER BY total_users DESC
	
-- Q3. Which countries contribute the most users?
	SELECT
		country,
		COUNT(user_id) as total_users
	FROM users
	GROUP BY country
	ORDER BY total_users DESC

-- Q4. Which acquisition channels generate users who become paying customers?
	SELECT 
		acquisition_channel,
		COUNT(DISTINCT u.user_id) as total_users,
		COUNT(CASE WHEN s.monthly_price > 0 THEN s.user_id END) as paying_users,
		ROUND(
			100.0 * COUNT(CASE WHEN s.monthly_price > 0 THEN s.user_id END) / COUNT(DISTINCT u.user_id)
			,2) as paid_conversion_pct
	 FROM users u
	 LEFT JOIN subscriptions s
	 	ON u.user_id = s.user_id
	 GROUP BY acquisition_channel
	 ORDER BY paid_conversion_pct DESC;


-- 2. Product Engagement — 4
--------------------------------------------------------
-- Q5. What is the average number of sessions per user?
	SELECT 
		COUNT(*) as total_sessions,
		COUNT(DISTINCT user_id) as active_users,
		ROUND(COUNT(*)::Numeric / COUNT(DISTINCT user_id), 2) AS avg_session_per_user
	FROM sessions
	
-- Q6. How does user engagement vary by subscription plan?
	SELECT
    	u.initial_plan AS plan_type,
    	COUNT(DISTINCT u.user_id) AS users,
    	COUNT(s.session_id) AS total_sessions,
    	ROUND(
        	AVG(s.session_duration_minutes), 2) AS avg_session_minutes,
    	ROUND(
        	AVG(s.pages_viewed), 2) AS avg_pages_per_session
	FROM users u
	LEFT JOIN sessions s
    	ON u.user_id = s.user_id
	GROUP BY u.initial_plan
	ORDER BY total_sessions DESC;
	
-- Q7. Which product features are used most frequently?
	SELECT feature_name,
		COUNT(*) as total_events
	FROM product_events
	GROUP BY feature_name
	ORDER BY total_events DESC

-- Q8. Are highly engaged users more likely to become paying customers?
	With engagement_groups as (
		SELECT 
			user_id,
			COUNT(*) as total_sessions,
			CASE
				WHEN COUNT(*) >= 100 THEN 'High Engagement'
				WHEN COUNT(*) >= 40 THEN 'Medium Engagement'
				WHEN COUNT(*) <= 40 THEN 'Low Engagement'
			END as engagement_group
		FROM sessions
		GROUP BY user_id
		ORDER BY total_sessions DESC
	)
	Select
		e.engagement_group,
		COUNT(DISTINCT e.user_id) as Users,
		COUNT(DISTINCT s.user_id) as Paying_customers,
		ROUND(100.0 * COUNT(DISTINCT s.user_id) / COUNT(DISTINCT e.user_id), 2) AS paid_conversion_pct
	FROM engagement_groups e
	LEFT JOIN subscriptions s
		ON e.user_id = s.user_id
		AND s.monthly_price > 0
	GROUP BY e.engagement_group
	ORDER BY paid_conversion_pct DESC;
		
-- 3. Funnel & Conversion — 3
--------------------------------------------------------
-- Q9. How many users move through each stage of the product funnel?
--     Signup → Login → Core Feature → Trial → Paid
	SELECT 
		COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'login') as login_users,
		COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'dashboard_view') as dashboard_users,
		COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'project_created') as project_users,
		COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'team_invited') as collaboration_users
	FROM product_events
	
-- Q10. Where is the biggest drop-off in the conversion funnel?
	WITH funnel as (
		SELECT 
			COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'login') as login_users,
			COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'dashboard_view') as dashboard_users,
			COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'project_created') as project_users,
			COUNT(DISTINCT user_id) FILTER(WHERE event_name = 'team_invited') as collaboration_users
		FROM product_events
	)
	SELECT 
		login_users,
		dashboard_users,
		project_users,
		collaboration_users,
		ROUND(100.0 * (login_users - dashboard_users) / NULLIF(login_users, 0), 2) as login_to_dashboard_drop_pct,
		ROUND(100.0 * (dashboard_users - project_users) / NULLIF(dashboard_users, 0), 2) as dashboard_to_project_drop_pct,
		ROUND(100.0 * (project_users - collaboration_users) / NULLIF(project_users, 0), 2) as project_to_collaboration_drop_pct
	FROM funnel;
	
-- Q11. Which acquisition channels have the highest user-to-paid conversion rate?
	SELECT 
		u.acquisition_channel,
		COUNT(DISTINCT u.user_id) as users,
		COUNT(DISTINCT 
		CASE
			WHEN s.monthly_price > 0 THEN u.user_id
		END) as paid_users,
		ROUND(100.0 * COUNT(DISTINCT CASE WHEN s.monthly_price > 0 THEN u.user_id END)
		/ COUNT(DISTINCT u.user_id), 2) as paid_conversion_pct
	FROM users u
	LEFT JOIN subscriptions s
		ON u.user_id = s.user_id
	GROUP BY u.acquisition_channel
	ORDER BY paid_conversion_pct DESC;
	
-- 4. Subscription & Revenue — 5
--------------------------------------------------------
-- Q12. How are subscriptions distributed across Free, Basic, Pro and Enterprise plans?
	Select 
		plan_type,
		COUNT(DISTINCT user_id) as total_users,
		COUNT(*) as subscriptions
	FROM subscriptions
	GROUP BY plan_type
	ORDER BY subscriptions DESC;

-- Q13. How many users upgrade or downgrade between subscription plans?
    WITH plan_history as(
		SELECT
	        user_id,
	        plan_type,
	        start_date,
	        LAG(plan_type) OVER (PARTITION BY user_id ORDER BY start_date) AS previous_plan
	    FROM subscriptions
	)
	SELECT 
		previous_plan,
		plan_type as new_plan,
		COUNT(*) as transactions
	FROM plan_history
		WHERE previous_plan IS NOT NULL
		AND previous_plan != plan_type
	GROUP BY previous_plan, plan_type
	ORDER BY transactions DESC;
	
-- Q14. How has monthly revenue changed over time?
	SELECT 
		DATE_TRUNC('month', transaction_date)::date as months,
		SUM(amount) as total_revenue
	FROM transactions
	WHERE transaction_status = 'Successful'
	GROUP BY 1
	ORDER BY 1;

-- Q15. Which subscription plans generate the most revenue?
	SELECT 
		s.plan_type,
		SUM(t.amount) as total_revenue
	FROM subscriptions s
	JOIN transactions t
		ON s.subscription_id = t.subscription_id
	WHERE transaction_status = 'Successful'
	GROUP BY s.plan_type
	ORDER BY total_revenue DESC;
	
-- Q16. Which customers or customer segments contribute the most revenue?
	SELECT
    	user_id,
    	SUM(amount) AS total_revenue
	FROM transactions
	WHERE transaction_status = 'Successful'
	GROUP BY user_id
	ORDER BY total_revenue DESC
	LIMIT 20;

-- 5. Retention & Churn — 5
--------------------------------------------------------
-- Q17. What is the overall customer churn rate?
	Select 
		COUNT(*) FILTER(WHERE account_status = 'Churned') as churned_users,
		COUNT(DISTINCT user_id) as total_users,
		ROUND(100.0 * COUNT(*) FILTER(WHERE account_status = 'Churned')
			/ COUNT(DISTINCT user_id),2) as churn_rate_pct
	FROM users;

-- Q18. Which subscription plans have the highest churn?
	SELECT 
		s.plan_type,
		COUNT(DISTINCT u.user_id) as total_users,
		COUNT(DISTINCT 
			CASE WHEN u.account_status = 'Churned' THEN u.user_id END) as churned_users,
		ROUND(
			100.0 * COUNT(DISTINCT CASE WHEN u.account_status = 'Churned' THEN u.user_id END)
			/ COUNT(DISTINCT u.user_id),2) as churned_rate_pct
	FROM subscriptions s
	JOIN users u
		ON s.user_id = u.user_id
	GROUP BY s.plan_type
	ORDER BY churned_rate_pct DESC;

-- Q19. Which acquisition channels have the best customer retention?
	SELECT 
		acquisition_channel,
		COUNT(DISTINCT user_id) as total_users,
		COUNT(*) FILTER(WHERE account_status != 'Churned') as retained_users,
		ROUND(100.0 * COUNT(*) FILTER(WHERE account_status != 'Churned')
			/ COUNT(DISTINCT user_id), 2) as retention_pct
	FROM users
	GROUP BY acquisition_channel
	ORDER BY retention_pct DESC;

-- Q20. How does product engagement differ between retained and churned users?
	SELECT 
		u.account_status,
		COUNT(DISTINCT u.user_id) as total_users,
		COUNT(s.session_id) as total_sessions,
		ROUND(AVG(s.session_duration_minutes),2) as avg_session_min,
		ROUND(AVG(s.pages_viewed),2) as avg_page_per_session
	FROM users u
	LEFT JOIN sessions s
		ON u.user_id = s.user_id
	GROUP BY u.account_status
	ORDER BY avg_session_min DESC;

-- Q21. Is higher support activity associated with higher customer churn?
	WITH ticket_counts as (
		Select 
			user_id,
			COUNT(*) as ticket_count
		FROM support_tickets
		GROUP BY user_id
	)
	Select 
		CASE
			WHEN t.ticket_count >= 3 THEN '3+ Tickets'
			WHEN t.ticket_count = 2 THEN '2 Tickets'
			WHEN t.ticket_count = 1 THEN '1 Ticket'
			ELSE 'No Ticket'
		END as Ticket_level,
		COUNT(*) as total_users,
		COUNT(*) FILTER(WHERE u.account_status = 'Churned') as churned_users,
		ROUND(
			100.0 * COUNT(*) FILTER(WHERE u.account_status = 'Churned')
			/ COUNT(*), 2) as Churn_rate_pct
	FROM ticket_counts t
	RIGHT JOIN users u
		ON t.user_id = u.user_id
	GROUP BY Ticket_level
	ORDER BY Churn_rate_pct DESC;
	
-- 6. Marketing & Support — 3
--------------------------------------------------------
-- Q22. Which marketing channels have the best CTR and conversion performance?
	SELECT 
		channel,
		SUM(impressions) as total_impressions,
		SUM(clicks) as total_clicks,
		SUM(conversion) as total_conversion,
		ROUND(
			100.0 * SUM(clicks) / NULLIF(SUM(impressions),0), 2) as CTR_pct,
		ROUND(
			100.0 * SUM(conversion) / NULLIF(SUM(clicks),0), 2) as conversion_rate_pct
	FROM marketing_campaigns
	GROUP BY channel
	ORDER BY CTR_pct DESC, conversion_rate_pct DESC;

-- Q23. Which marketing channels have the lowest customer acquisition cost?
	SELECT 
		channel,
		SUM(spend) as total_spend,
		SUM(conversion) as total_conversions,
		ROUND(
			SUM(spend) / NULLIF(SUM(conversion), 0), 2) as acquisition_cost
	FROM marketing_campaigns
	GROUP BY channel
	ORDER BY acquisition_cost DESC;
	
-- Q24. Which support-ticket categories are most common, and how do they relate to customer outcomes?
	SELECT 
		st.category,
		COUNT(*) as tickets,
		COUNT(DISTINCT st.user_id) as affected_users,
		ROUND(AVG(st.resolution_time_hours), 2) as avg_resolution_time,
		ROUND(AVG(st.customer_rating), 2) as avg_customer_rating,
		COUNT(DISTINCT 
			CASE WHEN u.account_status = 'Churned' THEN st.user_id END
		) as churned_users
	FROM support_tickets st
	JOIN users u
		ON st.user_id = u.user_id 
	GROUP BY category
	ORDER BY churned_users DESC;







	





