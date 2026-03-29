from fpdf import FPDF

class AriaPDF(FPDF):
    def __init__(self):
        super().__init__('L', 'mm', 'A4')  # Landscape
        self.set_auto_page_break(auto=False)

    def dark_bg(self):
        self.set_fill_color(15, 15, 20)
        self.rect(0, 0, 297, 210, 'F')

    def section_title(self, text, y):
        self.set_xy(20, y)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, text.upper(), ln=True)
        self.set_draw_color(40, 40, 50)
        self.line(20, y + 7, 277, y + 7)


def generate_architecture():
    pdf = AriaPDF()
    pdf.add_page()
    pdf.dark_bg()

    # Title
    pdf.set_xy(0, 12)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(297, 12, 'ARIA', align='C', ln=True)

    pdf.set_xy(0, 26)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(297, 6, 'DISTRIBUTED EDGE AI ARCHITECTURE', align='C', ln=True)

    # Three columns
    col_w = 75
    col_h = 120
    start_y = 40
    gap = 3
    # Total: 20 + 75 + 3 + 80 + 3 + 75 + 20 = 276 (fits in 297mm landscape)
    cols = [
        {
            'x': 20,
            'label': 'LAYER 1',
            'title': 'Companion Device',
            'chip': 'ESP32',
            'color': (74, 158, 255),
            'items': [
                ('Push Button', 'GPIO 0 - start/stop conversation'),
                ('ST7789 TFT Display', '240x320 SPI, word-wrapped responses'),
                ('4x RGB PWM LEDs', 'Sine-wave breathing animations'),
                ('WiFi State Machine', 'Auto-connects to Pi hotspot'),
                ('WebSocket Client', 'Bidirectional state sync + keepalive'),
                ('3D-Printed Enclosure', 'Custom Autodesk Inventor design'),
            ]
        },
        {
            'x': 20 + col_w + gap,
            'label': 'LAYER 2',
            'title': 'Edge AI Brain',
            'chip': 'Raspberry Pi 5',
            'color': (74, 255, 158),
            'items': [
                ('FastAPI Server', '3 WebSocket channels, REST API'),
                ('GPT-5.2 Agentic Brain', '10 tools, 6-iteration reasoning loop'),
                ('OpenAI Realtime API', '24kHz voice-to-voice, server VAD'),
                ('Whisper STT', 'Ambient transcription + filtering'),
                ('3-Tier TTS', 'ElevenLabs > OpenAI > espeak'),
                ('Memory Engine', 'Auto-extracts facts every 15 min'),
                ('SQLite (5 tables)', 'Transcripts, memories, calendar'),
                ('Bluetooth Audio', 'AirPods I/O via ALSA'),
            ]
        },
        {
            'x': 20 + col_w + gap + col_w + 5 + gap,
            'label': 'LAYER 3',
            'title': 'Live Dashboard',
            'chip': 'Browser',
            'color': (255, 74, 158),
            'items': [
                ('Animated Waveform', 'State-driven color and amplitude'),
                ('Live Transcript Feed', 'User, ARIA, Ambient speakers'),
                ('Conversation History', 'Full chat log with timestamps'),
                ('Tool Activity Log', 'Real-time tool calls + results'),
                ('Memory Viewer', 'What ARIA has learned about you'),
                ('Voice + Text Input', 'Web Speech API, zero polling'),
            ]
        },
    ]

    for col in cols:
        r, g, b = col['color']
        x = col['x']
        w = col_w if col != cols[1] else col_w + 10

        # Column background
        pdf.set_fill_color(22, 22, 32)
        pdf.set_draw_color(r // 3, g // 3, b // 3)
        pdf.rect(x, start_y, w, col_h, style='DF')

        # Layer label
        pdf.set_xy(x + 6, start_y + 4)
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(30, 4, col['label'])

        # Title
        pdf.set_xy(x + 6, start_y + 9)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(r, g, b)
        pdf.cell(60, 6, col['title'])

        # Chip
        pdf.set_xy(x + 6, start_y + 16)
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_fill_color(r // 4, g // 4, b // 4)
        pdf.set_text_color(r, g, b)
        chip_w = pdf.get_string_width(col['chip']) + 6
        pdf.cell(chip_w, 5, col['chip'], fill=True)

        # Items
        item_y = start_y + 25
        for name, desc in col['items']:
            pdf.set_fill_color(30, 30, 42)
            pdf.rect(x + 4, item_y, w - 8, 10, style='F')

            pdf.set_xy(x + 7, item_y + 1)
            pdf.set_font('Helvetica', 'B', 7)
            pdf.set_text_color(210, 210, 210)
            pdf.cell(50, 4, name)

            pdf.set_xy(x + 7, item_y + 5)
            pdf.set_font('Helvetica', '', 6)
            pdf.set_text_color(140, 140, 140)
            pdf.cell(65, 4, desc)

            item_y += 12

    # No floating connectors - columns sit side by side, clean and tight

    # Data flow bar
    flow_y = 166
    pdf.set_fill_color(22, 22, 32)
    pdf.set_draw_color(40, 40, 50)
    pdf.rect(20, flow_y, 257, 14, style='DF')

    steps = ['Button Press', '>', 'Voice Stream (24kHz)', '>', 'GPT-5.2 + Tools', '>', 'ElevenLabs TTS', '>', 'AirPods Output']
    pdf.set_xy(28, flow_y + 3)
    for step in steps:
        if step == '>':
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(12, 8, '>', align='C')
        else:
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(200, 200, 200)
            pdf.cell(pdf.get_string_width(step) + 6, 8, step)

    # APIs bar
    api_y = 184
    pdf.set_fill_color(22, 22, 32)
    pdf.set_draw_color(40, 40, 50)
    pdf.rect(20, api_y, 257, 14, style='DF')

    pdf.set_xy(24, api_y + 3)
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(35, 8, '7 APIs INTEGRATED')

    apis = [
        ('OpenAI Realtime', (16, 163, 127)),
        ('GPT-5.2', (16, 163, 127)),
        ('Whisper', (16, 163, 127)),
        ('OpenAI TTS', (16, 163, 127)),
        ('ElevenLabs', (255, 140, 90)),
        ('Brave Search', (251, 122, 91)),
        ('X / Twitter', (91, 188, 247)),
    ]
    x_pos = 62
    for name, (ar, ag, ab) in apis:
        pdf.set_fill_color(ar // 6, ag // 6, ab // 6)
        pdf.set_text_color(ar, ag, ab)
        w = pdf.get_string_width(name) + 8
        pdf.set_xy(x_pos, api_y + 3.5)
        pdf.set_font('Helvetica', 'B', 6.5)
        pdf.cell(w, 7, name, fill=True, align='C')
        x_pos += w + 4

    # Stats at bottom of columns area - removed to avoid overlap
    # The flow bar and APIs bar serve as the bottom info

    pdf.output('c:/Users/alvar/github-repos/bathHackathon/docs/ARIA_Architecture.pdf')
    print('Architecture PDF generated.')


def generate_commercial():
    pdf = AriaPDF()

    # PAGE 1: Competitor Landscape + Unit Economics
    pdf.add_page()
    pdf.dark_bg()

    # Title
    pdf.set_xy(0, 10)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(297, 12, 'ARIA', align='C', ln=True)

    pdf.set_xy(0, 23)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(297, 6, 'COMMERCIAL VIABILITY & MARKET POSITION', align='C', ln=True)

    # Competitor table
    pdf.section_title('Competitor Landscape - $435M raised, none delivered', 36)

    headers = ['Company', 'Funding', 'Status', 'Device Price', 'Subscription', 'Key Issue']
    col_widths = [38, 28, 36, 30, 30, 95]
    table_x = 20
    table_y = 48

    # Header row
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_text_color(100, 100, 100)
    x = table_x
    for i, h in enumerate(headers):
        pdf.set_xy(x, table_y)
        pdf.cell(col_widths[i], 8, h.upper())
        x += col_widths[i]

    # Data rows
    competitors = [
        ('Humane AI Pin', '$230M', 'Failed / Recalled', '$699', '$24/mo', 'Overheating, terrible UX, shut down', 'failed'),
        ('Rabbit R1', '$180M', 'Struggling', '$199', 'None', 'Android app wrapper, not real AI', 'struggling'),
        ('Limitless', '$25M', 'Early', '$99', '$19/mo', 'Record-only, no actions, no voice output', 'early'),
        ('Tab AI', '$2M', 'Early', '$49', '$8/mo', 'Closed-source, limited tools', 'early'),
    ]

    row_y = table_y + 10
    for name, funding, status, price, sub, issue, stype in competitors:
        pdf.set_draw_color(30, 30, 40)
        pdf.line(table_x, row_y + 11, table_x + 257, row_y + 11)

        x = table_x
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(col_widths[0], 10, name)

        x += col_widths[0]
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 100, 100)
        pdf.cell(col_widths[1], 10, funding)

        x += col_widths[1]
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', 'B', 7)
        if stype == 'failed':
            pdf.set_text_color(255, 80, 80)
        elif stype == 'struggling':
            pdf.set_text_color(255, 170, 70)
        else:
            pdf.set_text_color(150, 150, 150)
        pdf.cell(col_widths[2], 10, status)

        x += col_widths[2]
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(col_widths[3], 10, price)

        x += col_widths[3]
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(col_widths[4], 10, sub)

        x += col_widths[4]
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(140, 140, 140)
        pdf.cell(col_widths[5], 10, issue)

        row_y += 13

    # ARIA row (highlighted)
    pdf.set_fill_color(20, 40, 30)
    pdf.set_draw_color(74, 255, 158)
    pdf.rect(table_x - 2, row_y - 1, 261, 13, style='DF')

    x = table_x
    items_aria = [
        ('ARIA', 'B', 10, (74, 255, 158)),
        ('$0', 'B', 8, (74, 255, 158)),
        ('Live & Working', 'B', 7, (74, 255, 158)),
        ('~$30', 'B', 8, (74, 255, 158)),
        ('$0 self-hosted', '', 8, (74, 255, 158)),
        ('Open-source, private, works anywhere', '', 7, (74, 255, 158)),
    ]
    for i, (text, style, size, color) in enumerate(items_aria):
        pdf.set_xy(x, row_y)
        pdf.set_font('Helvetica', style, size)
        pdf.set_text_color(*color)
        pdf.cell(col_widths[i], 10, text)
        x += col_widths[i]

    # Unit Economics section
    econ_y = 120
    # No section title - cards speak for themselves
    pass

    cards = [
        ('BILL OF MATERIALS', '$16', 'ESP32 + Display + LEDs + Button + 3D Print', None),
        ('RETAIL KIT PRICE', '$149', 'Companion + setup guide + firmware', None),
        ('GROSS MARGIN', '89%', '$133 profit per kit sold', (74, 255, 158)),
        ('CLOUD COST', '$0', 'Runs on your own Pi 5', None),
    ]

    card_w = 55
    card_gap = 4
    card_x = 22
    card_y = econ_y + 12

    for label, value, detail, accent in cards:
        pdf.set_fill_color(22, 22, 32)
        pdf.set_draw_color(40, 40, 50)
        if accent:
            pdf.set_draw_color(accent[0] // 3, accent[1] // 3, accent[2] // 3)
            pdf.set_fill_color(20, 35, 25)
        pdf.rect(card_x, card_y, card_w, 38, style='DF')

        pdf.set_xy(card_x + 6, card_y + 5)
        pdf.set_font('Helvetica', '', 6.5)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(50, 4, label)

        pdf.set_xy(card_x + 6, card_y + 12)
        pdf.set_font('Helvetica', 'B', 24)
        if accent:
            pdf.set_text_color(*accent)
        else:
            pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 10, value)

        pdf.set_xy(card_x + 6, card_y + 26)
        pdf.set_font('Helvetica', '', 6.5)
        pdf.set_text_color(130, 130, 130)
        pdf.cell(50, 4, detail)

        card_x += card_w + card_gap

    # Margin bar
    bar_y = econ_y + 54
    bar_x = 20
    bar_w = 257
    pdf.set_fill_color(22, 22, 32)
    pdf.set_draw_color(40, 40, 50)
    pdf.rect(bar_x, bar_y, bar_w, 22, style='DF')

    pdf.set_xy(bar_x + 6, bar_y + 2)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(80, 6, 'Revenue Breakdown Per $149 Kit')

    pdf.set_xy(bar_x + 200, bar_y + 2)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(74, 255, 158)
    pdf.cell(50, 6, '89% margin', align='R')

    # The bar itself
    bar_inner_y = bar_y + 11
    bar_inner_x = bar_x + 6
    bar_inner_w = 245

    # Cost portion (11%)
    cost_w = bar_inner_w * 0.11
    pdf.set_fill_color(255, 100, 100)
    pdf.rect(bar_inner_x, bar_inner_y, cost_w, 8, style='F')
    pdf.set_xy(bar_inner_x, bar_inner_y + 1)
    pdf.set_font('Helvetica', 'B', 6)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(cost_w, 6, '$16', align='C')

    # Profit portion (89%)
    profit_w = bar_inner_w * 0.89
    pdf.set_fill_color(42, 138, 90)
    pdf.rect(bar_inner_x + cost_w + 1, bar_inner_y, profit_w, 8, style='F')
    pdf.set_xy(bar_inner_x + cost_w + 1, bar_inner_y + 1)
    pdf.set_font('Helvetica', 'B', 6)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(profit_w, 6, '$133 profit', align='C')

    # PAGE 2: Traction + Revenue Model
    pdf.add_page()
    pdf.dark_bg()

    # Traction
    pdf.section_title('Traction - Validated During the Hackathon', 14)

    traction = [
        ('60+', 'WAITLIST SIGNUPS', 'Organic interest within 24 hours', (74, 158, 255)),
        ('100+', 'B2B PROSPECTS', 'LinkedIn outreach to professionals', (74, 158, 255)),
        ('24h', 'BUILD TIME', 'Hardware + software + 3D print', (255, 255, 255)),
        ('$0', 'MARKETING SPEND', 'All traction fully organic', (255, 255, 255)),
    ]

    t_x = 20
    t_y = 28
    t_w = 60

    for value, label, detail, color in traction:
        pdf.set_fill_color(22, 22, 32)
        pdf.set_draw_color(40, 40, 50)
        pdf.rect(t_x, t_y, t_w, 42, style='DF')

        pdf.set_xy(t_x, t_y + 6)
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(*color)
        pdf.cell(t_w, 12, value, align='C')

        pdf.set_xy(t_x, t_y + 22)
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(t_w, 5, label, align='C')

        pdf.set_xy(t_x, t_y + 30)
        pdf.set_font('Helvetica', '', 6.5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(t_w, 5, detail, align='C')

        t_x += t_w + 5.7

    # Revenue Model
    pdf.section_title('Revenue Model', 80)

    tiers = [
        ('OPEN SOURCE', 'Free', 'forever', ['Full source code', 'Self-hosted on your Pi', 'All 10 tools', 'Community support'], (180, 180, 180), (40, 40, 50)),
        ('ARIA KIT', '$149', 'one-time', ['Pre-built companion', 'Pre-flashed firmware', 'Setup guide', 'Voice clone setup'], (74, 158, 255), (20, 30, 60)),
        ('ARIA PRO', '$9/mo', 'subscription', ['Cloud-hosted brain', 'Premium voices', 'Mobile app', 'Priority support'], (74, 255, 158), (20, 50, 30)),
        ('ENTERPRISE', 'Custom', 'per seat', ['Meeting intelligence', 'Sales coaching', 'Team memory sharing', 'SSO + compliance'], (255, 215, 0), (50, 45, 15)),
    ]

    tier_x = 20
    tier_y = 94
    tier_w = 60

    for name, price, period, features, color, bg in tiers:
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(color[0] // 3, color[1] // 3, color[2] // 3)
        pdf.rect(tier_x, tier_y, tier_w, 70, style='DF')

        pdf.set_xy(tier_x + 6, tier_y + 5)
        pdf.set_font('Helvetica', '', 6.5)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(40, 4, name)

        pdf.set_xy(tier_x + 6, tier_y + 12)
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(*color)
        pdf.cell(40, 10, price)

        pdf.set_xy(tier_x + 6, tier_y + 24)
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(40, 4, period)

        feat_y = tier_y + 34
        for feat in features:
            pdf.set_xy(tier_x + 6, feat_y)
            pdf.set_font('Helvetica', '', 7)
            pdf.set_text_color(74, 255, 158)
            pdf.cell(4, 5, '+')
            pdf.set_text_color(160, 160, 160)
            pdf.cell(46, 5, '  ' + feat)
            feat_y += 7

        tier_x += tier_w + 5.7

    # Bottom line
    bl_y = 175
    pdf.set_fill_color(20, 40, 30)
    pdf.set_draw_color(74, 255, 158)
    pdf.rect(20, bl_y, 257, 18, style='DF')

    pdf.set_xy(20, bl_y + 3)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(257, 5, 'Competitors raised $435M combined and failed to ship what we built in 24 hours for $30.', align='C')

    pdf.set_xy(20, bl_y + 9)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(74, 255, 158)
    pdf.cell(257, 5, 'ARIA works today. It works on any network, anywhere. And 60+ people already want one.', align='C')

    pdf.output('c:/Users/alvar/github-repos/bathHackathon/docs/ARIA_Commercial.pdf')
    print('Commercial PDF generated.')


if __name__ == '__main__':
    generate_architecture()
    generate_commercial()
