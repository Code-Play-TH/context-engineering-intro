## FEATURE:

- facebook ads , google ads , tiktok ads scraper
- can setup daily cronjob to scrap ads data

## EXAMPLES:

The user interface is the most critical part. It must be intuitive and clean.

Example 1: The Empty State

Explanation: When a new user visits the site for the first time, the screen should be mostly empty to maintain a minimal feel. It should clearly guide them on what to do next.

Visual: A clean page with a single, centered button labeled + Add Your First Ad Account.

Example 2: The Populated Dashboard

Explanation: After the user has connected a few accounts, the dashboard will display a grid of cards. Each card represents one ad account. This view gives a quick, high-level overview of all connected platforms.

Visual: A responsive grid of cards. A Facebook card next to a Google Ads card, each showing the account name and today's ad spend.

Example 3: The "Add Account" Modal

Explanation: When the user clicks the "Add New Account" button, a simple, non-intrusive modal or pop-up appears, showing the three platform choices with their logos.

Visual: A small, centered box with three buttons: [f] Connect with Facebook, [G] Connect with Google, [t] Connect with TikTok.

## DOCUMENTATION:

- https://developers.facebook.com/docs/
- https://developers.google.com/google-ads/api
- https://developers.tiktok.com/doc/overview
- https://business-api.tiktok.com/portal/docs

## OTHER CONSIDERATIONS:

- Documentation: Include a comprehensive README.md file with clear instructions on how to install, configure, and run the project locally to ensure smooth onboarding and setup.
- Code Quality: Ensure all code follows clean code principles and aligns with the SOLID design principles to maintain readability, scalability, and maintainability.
- Authentication & Security: The system must use OAuth 2.0 to connect to ad accounts for maximum security. DO NOT store user credentials (usernames/passwords). Only store the access tokens obtained.
- API Rate Limiting: The generated code must handle the rate limits of each API properly to prevent the system from being blocked for making too many requests. This should include implementing delays or sleep calls between requests.
- Error Handling: The system must have robust error handling. For instance, if one platform's API is unresponsive, the system should not crash. It should continue its work and log the error.
