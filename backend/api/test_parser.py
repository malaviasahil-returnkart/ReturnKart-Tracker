"""
RETURNKART.IN — EMAIL PARSER TEST PAGE
Serves a simple HTML page at /test-parser for testing email parsing.
No authentication needed. Only available in non-production or via direct URL.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from backend.tests.sample_emails import SAMPLE_EMAILS, get_all_sample_names

router = APIRouter()


@router.get("/test-parser", response_class=HTMLResponse)
async def test_parser_page():
    """Serve a simple test page for email parsing."""
    # Build options for the dropdown
    options = "".join(
        f'<option value="{name}">{name.replace("_", " ").title()}</option>'
        for name in get_all_sample_names()
    )

    # Build the sample emails as a JS object
    import json
    samples_js = json.dumps(SAMPLE_EMAILS)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ReturnKart — Email Parser Tester</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0a0a0a; color: #e5e5e5; font-family: -apple-system, system-ui, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #f5c518; margin-bottom: 8px; font-size: 24px; }}
        p.sub {{ color: #888; font-size: 13px; margin-bottom: 24px; }}
        label {{ color: #aaa; font-size: 13px; display: block; margin-bottom: 6px; }}
        select, textarea, input {{ width: 100%; background: #1a1a1a; color: #e5e5e5; border: 1px solid #333; border-radius: 8px; padding: 10px; font-size: 14px; font-family: monospace; }}
        select:focus, textarea:focus {{ border-color: #f5c518; outline: none; }}
        textarea {{ min-height: 300px; resize: vertical; margin-bottom: 12px; }}
        .row {{ display: flex; gap: 12px; margin-bottom: 16px; }}
        .row > * {{ flex: 1; }}
        button {{ background: #f5c518; color: #0a0a0a; border: none; border-radius: 8px; padding: 12px 24px; font-size: 15px; font-weight: 600; cursor: pointer; width: 100%; margin-bottom: 20px; }}
        button:hover {{ background: #ddb315; }}
        button:disabled {{ background: #555; color: #888; cursor: not-allowed; }}
        .result {{ background: #111; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-top: 12px; }}
        .result h3 {{ color: #f5c518; margin-bottom: 12px; font-size: 16px; }}
        .field {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #222; }}
        .field .label {{ color: #888; font-size: 13px; }}
        .field .value {{ color: #e5e5e5; font-size: 13px; font-weight: 500; text-align: right; max-width: 60%; }}
        .success {{ color: #22c55e; }}
        .fail {{ color: #ef4444; }}
        .confidence {{ font-size: 20px; font-weight: bold; }}
        .spinner {{ display: inline-block; width: 16px; height: 16px; border: 2px solid #f5c518; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        .badge-high {{ background: #166534; color: #22c55e; }}
        .badge-med {{ background: #713f12; color: #f59e0b; }}
        .badge-low {{ background: #7f1d1d; color: #ef4444; }}
    </style>
</head>
<body>
    <h1>🧪 Email Parser Tester</h1>
    <p class="sub">Feed sample emails into Gemini AI and see what it extracts. No Gmail needed.</p>

    <div class="row">
        <div>
            <label>Load Sample Email</label>
            <select id="sampleSelect" onchange="loadSample()">
                <option value="">-- Select a brand --</option>
                {options}
                <option value="custom">Custom (paste your own)</option>
            </select>
        </div>
        <div>
            <label>Platform Hint</label>
            <input type="text" id="platformInput" placeholder="amazon, flipkart, hm, unknown..." value="unknown">
        </div>
    </div>

    <label>Email Text (Subject + From + Body)</label>
    <textarea id="emailText" placeholder="Subject: Your order #12345 is confirmed\nFrom: noreply@brand.com\nDate: ...\n\nHello, your order details..."></textarea>

    <button id="parseBtn" onclick="parseEmail()">🤖 Parse with Gemini AI</button>

    <div id="resultArea"></div>

    <script>
    const SAMPLES = {samples_js};

    function loadSample() {{
        const name = document.getElementById('sampleSelect').value;
        if (name && name !== 'custom' && SAMPLES[name]) {{
            document.getElementById('emailText').value = SAMPLES[name].email_text;
            document.getElementById('platformInput').value = SAMPLES[name].platform;
        }} else {{
            document.getElementById('emailText').value = '';
            document.getElementById('platformInput').value = 'unknown';
        }}
    }}

    async function parseEmail() {{
        const btn = document.getElementById('parseBtn');
        const emailText = document.getElementById('emailText').value;
        const platform = document.getElementById('platformInput').value || 'unknown';
        const resultArea = document.getElementById('resultArea');

        if (!emailText.trim()) {{
            resultArea.innerHTML = '<div class="result"><p class="fail">Please enter email text to parse.</p></div>';
            return;
        }}

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Gemini is analyzing...';
        resultArea.innerHTML = '';

        try {{
            const res = await fetch('/api/orders/test-parse', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ email_text: emailText, platform: platform }})
            }});
            const data = await res.json();

            if (data.success && data.extracted) {{
                const e = data.extracted;
                const conf = e.confidence || 0;
                const confClass = conf >= 0.8 ? 'badge-high' : conf >= 0.5 ? 'badge-med' : 'badge-low';
                const confLabel = conf >= 0.8 ? 'HIGH' : conf >= 0.5 ? 'MEDIUM' : 'LOW';

                resultArea.innerHTML = `
                    <div class="result">
                        <h3 class="success">✅ Order Extracted Successfully</h3>
                        <div class="field"><span class="label">Confidence</span><span class="value"><span class="confidence">${{(conf * 100).toFixed(0)}}%</span> <span class="badge ${{confClass}}">${{confLabel}}</span></span></div>
                        <div class="field"><span class="label">Order ID</span><span class="value">${{e.order_id || 'null'}}</span></div>
                        <div class="field"><span class="label">Brand</span><span class="value">${{e.brand || 'null'}}</span></div>
                        <div class="field"><span class="label">Item</span><span class="value">${{e.item_name || 'null'}}</span></div>
                        <div class="field"><span class="label">Price</span><span class="value">₹${{e.total_amount ? e.total_amount.toLocaleString('en-IN') : 'null'}}</span></div>
                        <div class="field"><span class="label">Order Date</span><span class="value">${{e.order_date || 'null'}}</span></div>
                        <div class="field"><span class="label">Category</span><span class="value">${{e.category || 'null'}}</span></div>
                        <div class="field"><span class="label">Courier</span><span class="value">${{e.courier_partner || 'null'}}</span></div>
                        <div class="field"><span class="label">Pincode</span><span class="value">${{e.delivery_pincode || 'null'}}</span></div>
                        <div class="field"><span class="label">Platform Hint</span><span class="value">${{data.platform_hint}}</span></div>
                    </div>
                `;
            }} else {{
                resultArea.innerHTML = `
                    <div class="result">
                        <h3 class="fail">❌ Extraction Failed</h3>
                        <p style="color:#888;margin-top:8px">${{data.message || 'Gemini could not parse this email.'}}</p>
                    </div>
                `;
            }}
        }} catch(err) {{
            resultArea.innerHTML = `<div class="result"><h3 class="fail">❌ Error</h3><p style="color:#888">${{err.message}}</p></div>`;
        }}

        btn.disabled = false;
        btn.innerHTML = '🤖 Parse with Gemini AI';
    }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
