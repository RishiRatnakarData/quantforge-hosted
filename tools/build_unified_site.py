import base64
import hashlib
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
src=root/'web'
html=(src/'site/site.template.html').read_text(encoding="utf-8")
nav='<button class="nav-btn" data-page="private">My workspace</button>'
html=html.replace('</nav>',nav+'</nav>',1)
block='''<section class="tabpage" id="page-private">
  <div class="pagehead"><h1>My workspace</h1><p id="private-status">Private · Sign in required</p></div>
  <div class="pane" id="private-login"><h3>Sign in</h3>
    <div class="formgrid" style="margin-top:14px">
      <div class="field"><label for="private-email">Email</label><input id="private-email" type="email" autocomplete="username" placeholder="Your private account"></div>
      <div class="field"><label for="private-password">Password</label><input id="private-password" type="password" autocomplete="current-password" placeholder="Password"></div>
    </div><div class="controls"><button class="btn primary" id="private-login-submit">Sign in</button><span class="tiny">Only the authorized owner account can sign in.</span></div>
  </div>
  <div id="private-mfa" class="pane" hidden>
    <h3 id="private-mfa-title">Authenticator verification</h3>
    <p id="private-mfa-instructions" class="tiny">Enter a six-digit code from your authenticator app.</p>
    <div id="private-mfa-setup-actions" hidden>
      <button class="btn" id="private-mfa-start">Start authenticator setup</button>
    </div>
    <div id="private-mfa-qr-wrap" hidden>
      <img id="private-mfa-qr" width="210" height="210" alt="Authenticator enrollment QR code" style="background:white;padding:8px;margin:12px 0" />
      <p class="tiny">Scan the code with an authenticator app. Keep the authenticator and its recovery options secure.</p>
    </div>
    <div class="field" style="max-width:220px;margin:14px 0">
      <label for="private-mfa-code">Six-digit code</label>
      <input id="private-mfa-code" type="text" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" />
    </div>
    <div class="controls"><button class="btn primary" id="private-mfa-submit">Verify authenticator</button>
      <button class="btn" id="private-mfa-logout">Sign out</button></div>
  </div>
  <div id="private-signed" hidden>
    <div class="controls"><span class="mini">Alpaca observations · Supabase private portfolio</span><button class="btn sm" id="private-logout">Sign out</button></div>
    <div class="pane"><div class="three">
      <div class="metric"><span class="muted">Virtual total</span><strong id="private-total">—</strong></div>
      <div class="metric"><span class="muted">Available cash</span><strong id="private-cash">—</strong></div>
      <div class="metric"><span class="muted">Invested value</span><strong id="private-invested">—</strong></div>
    </div><div class="section-title"><h3>Positions</h3></div><div id="private-positions"></div></div>
    <div class="pane"><h3>Market observation and virtual trade</h3>
      <div class="formgrid" style="margin-top:12px"><div class="field"><label for="private-symbol">Investment</label><select id="private-symbol"></select></div>
      <div class="field"><label for="private-side">Action</label><select id="private-side"><option value="buy">Buy with USD budget</option><option value="sell">Sell units</option></select></div>
      <div class="field"><label for="private-amount">USD budget / units</label><input type="number" min="0.00000001" step="any" id="private-amount" value="100"></div></div>
      <div class="controls"><button class="btn" id="private-quote-submit">Get market price</button><button class="btn primary" id="private-trade-submit">Record virtual trade</button></div>
      <div class="tiny" id="private-quote" style="margin-top:10px">No quote loaded</div>
      <p class="tiny">IEX stock/ETF trades or Alpaca crypto venue observations. Transactions require a fresh timestamp. No brokerage order is placed.</p>
    </div>
    <div class="pane"><h3>Research notes</h3><div class="field" style="margin-top:12px"><label for="private-note">Private note</label><textarea id="private-note" maxlength="2000" rows="3" placeholder="Why are you considering this investment?"></textarea></div>
      <div class="controls"><button class="btn" id="private-note-submit">Save note</button></div><div id="private-notes"></div>
      <p class="tiny">Watchlist: <span id="private-watchlist">None</span></p>
    </div>
    <div class="pane"><h3>Quant / valuation / ML</h3><p class="tiny">The other tabs currently run the public fictional demonstration models. They do not use your private market observations. Full server-backed analysis is a separate integration milestone.</p></div>
  </div>
  <p id="private-message" class="tiny" role="status" aria-live="polite"></p>
</section>'''
html=html.replace('<div class="footerline">',block+'\n<div class="footerline">',1)
html=html.replace('<script>/* QF_APP */</script>', '<script>/* QF_APP */</script>\n<script>/* QF_PRIVATE */</script>')
html=html.replace('All figures are fictional; none are market observations.','All demo figures are fictional; the private workspace uses a separate data source.')
html=html.replace('Methods are simplified client-side implementations for review.', 'Public analysis uses separate simplified client-side calculations; private positions use the authenticated API.')
html=html.replace('.navtop{display:none}', '#private-signed[hidden],#private-login[hidden],#private-mfa[hidden],#private-mfa-qr-wrap[hidden],#private-mfa-setup-actions[hidden]{display:none!important}#private-message{margin-top:8px}.navtop{display:none}')
html=html.replace('body></html>','body></html>')
# Ensure all app scripts stay CSP-protected; no external JS libraries.
for slot, file in [('/* QF_MODEL */','model.js'),('/* QF_APP */','app.js'),('/* QF_PRIVATE */','private.js')]:
 text=(src/'site'/file).read_text(encoding="utf-8").replace('</script','<\\/script')
 html=html.replace(slot,text)
(root/'public/index.html').write_text(html, encoding="utf-8")
scripts=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)
assert len(scripts)==3
hashes=["'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'" for s in scripts]
csp="default-src 'none'; script-src "+' '.join(hashes)+"; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
(root/'public/_headers').write_text("/*\n  Content-Security-Policy: "+csp+"\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n", encoding="utf-8")
print('Built',root/'public/index.html',len(html),'bytes',len(scripts),'protected scripts')
