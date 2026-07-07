from .models import Country, Language, PartOfSpeech, Image, CountryLanguage
from django.conf import settings
import os

def seed_countries(sender, **kwargs):
   if sender.name != 'dictApp':
      return

   countries = [
      # Africa
      Country(name="Algeria", iso_code="DZ"),
      Country(name="Angola", iso_code="AO"),
      Country(name="Benin", iso_code="BJ"),
      Country(name="Botswana", iso_code="BW"),
      Country(name="Burkina Faso", iso_code="BF"),
      Country(name="Burundi", iso_code="BI"),
      Country(name="Cameroon", iso_code="CM"),
      Country(name="Cape Verde", iso_code="CV"),
      Country(name="Central African Republic", iso_code="CF"),
      Country(name="Chad", iso_code="TD"),
      Country(name="Comoros", iso_code="KM"),
      Country(name="Congo (Democratic Republic)", iso_code="CD"),
      Country(name="Congo (Republic)", iso_code="CG"),
      Country(name="Djibouti", iso_code="DJ"),
      Country(name="Egypt", iso_code="EG"),
      Country(name="Equatorial Guinea", iso_code="GQ"),
      Country(name="Eritrea", iso_code="ER"),
      Country(name="Eswatini", iso_code="SZ"),
      Country(name="Ethiopia", iso_code="ET"),
      Country(name="Gabon", iso_code="GA"),
      Country(name="Gambia", iso_code="GM"),
      Country(name="Ghana", iso_code="GH"),
      Country(name="Guinea", iso_code="GN"),
      Country(name="Guinea-Bissau", iso_code="GW"),
      Country(name="Ivory Coast", iso_code="CI"),
      Country(name="Kenya", iso_code="KE"),
      Country(name="Lesotho", iso_code="LS"),
      Country(name="Liberia", iso_code="LR"),
      Country(name="Libya", iso_code="LY"),
      Country(name="Madagascar", iso_code="MG"),
      Country(name="Malawi", iso_code="MW"),
      Country(name="Mali", iso_code="ML"),
      Country(name="Mauritania", iso_code="MR"),
      Country(name="Mauritius", iso_code="MU"),
      Country(name="Morocco", iso_code="MA"),
      Country(name="Mozambique", iso_code="MZ"),
      Country(name="Namibia", iso_code="NA"),
      Country(name="Niger", iso_code="NE"),
      Country(name="Nigeria", iso_code="NG"),
      Country(name="Rwanda", iso_code="RW"),
      Country(name="Sao Tome and Principe", iso_code="ST"),
      Country(name="Senegal", iso_code="SN"),
      Country(name="Seychelles", iso_code="SC"),
      Country(name="Sierra Leone", iso_code="SL"),
      Country(name="Somalia", iso_code="SO"),
      Country(name="South Africa", iso_code="ZA"),
      Country(name="South Sudan", iso_code="SS"),
      Country(name="Sudan", iso_code="SD"),
      Country(name="Tanzania", iso_code="TZ"),
      Country(name="Togo", iso_code="TG"),
      Country(name="Tunisia", iso_code="TN"),
      Country(name="Uganda", iso_code="UG"),
      Country(name="Zambia", iso_code="ZM"),
      Country(name="Zimbabwe", iso_code="ZW"),
      # Asia
      Country(name="Afghanistan", iso_code="AF"),
      Country(name="Armenia", iso_code="AM"),
      Country(name="Azerbaijan", iso_code="AZ"),
      Country(name="Bahrain", iso_code="BH"),
      Country(name="Bangladesh", iso_code="BD"),
      Country(name="Bhutan", iso_code="BT"),
      Country(name="Brunei", iso_code="BN"),
      Country(name="Cambodia", iso_code="KH"),
      Country(name="China", iso_code="CN"),
      Country(name="Georgia", iso_code="GE"),
      Country(name="India", iso_code="IN"),
      Country(name="Indonesia", iso_code="ID"),
      Country(name="Iran", iso_code="IR"),
      Country(name="Iraq", iso_code="IQ"),
      Country(name="Israel", iso_code="IL"),
      Country(name="Japan", iso_code="JP"),
      Country(name="Jordan", iso_code="JO"),
      Country(name="Kazakhstan", iso_code="KZ"),
      Country(name="Kuwait", iso_code="KW"),
      Country(name="Kyrgyzstan", iso_code="KG"),
      Country(name="Laos", iso_code="LA"),
      Country(name="Lebanon", iso_code="LB"),
      Country(name="Malaysia", iso_code="MY"),
      Country(name="Maldives", iso_code="MV"),
      Country(name="Mongolia", iso_code="MN"),
      Country(name="Myanmar", iso_code="MM"),
      Country(name="Nepal", iso_code="NP"),
      Country(name="North Korea", iso_code="KP"),
      Country(name="Oman", iso_code="OM"),
      Country(name="Pakistan", iso_code="PK"),
      Country(name="Palestine", iso_code="PS"),
      Country(name="Philippines", iso_code="PH"),
      Country(name="Qatar", iso_code="QA"),
      Country(name="Saudi Arabia", iso_code="SA"),
      Country(name="Singapore", iso_code="SG"),
      Country(name="South Korea", iso_code="KR"),
      Country(name="Sri Lanka", iso_code="LK"),
      Country(name="Syria", iso_code="SY"),
      Country(name="Taiwan", iso_code="TW"),
      Country(name="Tajikistan", iso_code="TJ"),
      Country(name="Thailand", iso_code="TH"),
      Country(name="Timor-Leste", iso_code="TL"),
      Country(name="Turkey", iso_code="TR"),
      Country(name="Turkmenistan", iso_code="TM"),
      Country(name="United Arab Emirates", iso_code="AE"),
      Country(name="Uzbekistan", iso_code="UZ"),
      Country(name="Vietnam", iso_code="VN"),
      Country(name="Yemen", iso_code="YE"),
      # Europe
      Country(name="Albania", iso_code="AL"),
      Country(name="Andorra", iso_code="AD"),
      Country(name="Austria", iso_code="AT"),
      Country(name="Belarus", iso_code="BY"),
      Country(name="Belgium", iso_code="BE"),
      Country(name="Bosnia and Herzegovina", iso_code="BA"),
      Country(name="Bulgaria", iso_code="BG"),
      Country(name="Croatia", iso_code="HR"),
      Country(name="Cyprus", iso_code="CY"),
      Country(name="Czech Republic", iso_code="CZ"),
      Country(name="Denmark", iso_code="DK"),
      Country(name="Estonia", iso_code="EE"),
      Country(name="Finland", iso_code="FI"),
      Country(name="France", iso_code="FR"),
      Country(name="Germany", iso_code="DE"),
      Country(name="Greece", iso_code="GR"),
      Country(name="Hungary", iso_code="HU"),
      Country(name="Iceland", iso_code="IS"),
      Country(name="Ireland", iso_code="IE"),
      Country(name="Italy", iso_code="IT"),
      Country(name="Kosovo", iso_code="XK"),
      Country(name="Latvia", iso_code="LV"),
      Country(name="Liechtenstein", iso_code="LI"),
      Country(name="Lithuania", iso_code="LT"),
      Country(name="Luxembourg", iso_code="LU"),
      Country(name="Malta", iso_code="MT"),
      Country(name="Moldova", iso_code="MD"),
      Country(name="Monaco", iso_code="MC"),
      Country(name="Montenegro", iso_code="ME"),
      Country(name="Netherlands", iso_code="NL"),
      Country(name="North Macedonia", iso_code="MK"),
      Country(name="Norway", iso_code="NO"),
      Country(name="Poland", iso_code="PL"),
      Country(name="Portugal", iso_code="PT"),
      Country(name="Romania", iso_code="RO"),
      Country(name="Russia", iso_code="RU"),
      Country(name="San Marino", iso_code="SM"),
      Country(name="Serbia", iso_code="RS"),
      Country(name="Slovakia", iso_code="SK"),
      Country(name="Slovenia", iso_code="SI"),
      Country(name="Spain", iso_code="ES"),
      Country(name="Sweden", iso_code="SE"),
      Country(name="Switzerland", iso_code="CH"),
      Country(name="Ukraine", iso_code="UA"),
      Country(name="United Kingdom", iso_code="GB"),
      Country(name="Vatican City", iso_code="VA"),
      # North America
      Country(name="Antigua and Barbuda", iso_code="AG"),
      Country(name="Bahamas", iso_code="BS"),
      Country(name="Barbados", iso_code="BB"),
      Country(name="Belize", iso_code="BZ"),
      Country(name="Canada", iso_code="CA"),
      Country(name="Costa Rica", iso_code="CR"),
      Country(name="Cuba", iso_code="CU"),
      Country(name="Dominica", iso_code="DM"),
      Country(name="Dominican Republic", iso_code="DO"),
      Country(name="El Salvador", iso_code="SV"),
      Country(name="Grenada", iso_code="GD"),
      Country(name="Guatemala", iso_code="GT"),
      Country(name="Haiti", iso_code="HT"),
      Country(name="Honduras", iso_code="HN"),
      Country(name="Jamaica", iso_code="JM"),
      Country(name="Mexico", iso_code="MX"),
      Country(name="Nicaragua", iso_code="NI"),
      Country(name="Panama", iso_code="PA"),
      Country(name="Saint Kitts and Nevis", iso_code="KN"),
      Country(name="Saint Lucia", iso_code="LC"),
      Country(name="Saint Vincent and the Grenadines", iso_code="VC"),
      Country(name="Trinidad and Tobago", iso_code="TT"),
      Country(name="United States", iso_code="US"),
      # South America
      Country(name="Argentina", iso_code="AR"),
      Country(name="Bolivia", iso_code="BO"),
      Country(name="Brazil", iso_code="BR"),
      Country(name="Chile", iso_code="CL"),
      Country(name="Colombia", iso_code="CO"),
      Country(name="Ecuador", iso_code="EC"),
      Country(name="Guyana", iso_code="GY"),
      Country(name="Paraguay", iso_code="PY"),
      Country(name="Peru", iso_code="PE"),
      Country(name="Suriname", iso_code="SR"),
      Country(name="Uruguay", iso_code="UY"),
      Country(name="Venezuela", iso_code="VE"),
      # Oceania
      Country(name="Australia", iso_code="AU"),
      Country(name="Fiji", iso_code="FJ"),
      Country(name="Kiribati", iso_code="KI"),
      Country(name="Marshall Islands", iso_code="MH"),
      Country(name="Micronesia", iso_code="FM"),
      Country(name="Nauru", iso_code="NR"),
      Country(name="New Zealand", iso_code="NZ"),
      Country(name="Palau", iso_code="PW"),
      Country(name="Papua New Guinea", iso_code="PG"),
      Country(name="Samoa", iso_code="WS"),
      Country(name="Solomon Islands", iso_code="SB"),
      Country(name="Tonga", iso_code="TO"),
      Country(name="Tuvalu", iso_code="TV"),
      Country(name="Vanuatu", iso_code="VU"),
   ]

   Country.objects.bulk_create(countries, ignore_conflicts=True)

def seed_lang_and_parts_of_speech(sender, **kwargs):
   LANGUAGES_DATA = {
      "English": {
         "flag": "flags/English.webp",
         "pos": [
            "Noun", "Verb", "Adjective", "Adverb", "Pronoun",
            "Preposition", "Conjunction", "Interjection", "Article", "Determiner"
         ],
         "countries": [
            "United Kingdom", "United States", "Canada", "Australia",
            "New Zealand", "Ireland"
         ]
      },
      "Spanish": {
         "flag": "flags/Spanish.webp",
         "pos": [
            "Sustantivo", "Verbo", "Adjetivo", "Adverbio", "Pronombre",
            "Preposición", "Conjunción", "Interjección", "Artículo"
         ],
         "countries": [
            "Spain", "Mexico", "Argentina", "Colombia",
            "Venezuela", "Cuba"
        ]
      },
      "French": {
         "flag": "flags/French.webp",
         "pos": [
            "Nom", "Verbe", "Adjectif", "Adverbe", "Pronom",
            "Préposition", "Conjonction", "Interjection", "Article"
         ],
         "countries": [
            "France", "Belgium", "Switzerland", "Canada"
        ]
      },
      "German": {
         "flag": "flags/German.webp",
         "pos": [
            "Nomen", "Verb", "Adjektiv", "Adverb", "Pronomen",
            "Präposition", "Konjunktion", "Interjektion", "Artikel"
         ],
         "countries": [
            "Germany", "Austria", "Switzerland"
         ]
      },
      "Italian": {
         "flag": "flags/Italian.webp",
         "pos": [
            "Nome", "Verbo", "Aggettivo", "Avverbio", "Pronome",
            "Preposizione", "Congiunzione", "Interiezione", "Articolo"
         ],
         "countries": [
            "Italy", "San Marino", "Vatican City", "Switzerland"
         ]
      },
      "Portuguese": {
         "flag": "flags/Portuguese.webp",
         "pos": [
            "Substantivo", "Verbo", "Adjetivo", "Advérbio", "Pronome",
            "Preposição", "Conjunção", "Interjeição", "Artigo"
         ],
         "countries": [
            "Portugal", "Brazil"
         ]
      },
      "Russian": {
         "flag": "flags/Russian.webp",
         "pos": [
            "Существительное", "Глагол", "Прилагательное", "Наречие",
            "Местоимение", "Предлог", "Союз", "Междометие", "Частица"
         ],
         "countries": [
            "Russia", "Belarus", "Kazakhstan", "Kyrgyzstan"
         ]
      },
      "Japanese": {
         "flag": "flags/Japanese.webp",
         "pos": [
            "名詞 (Noun)", "動詞 (Verb)", "形容詞 (Adjective)",
            "副詞 (Adverb)", "助詞 (Particle)", "接続詞 (Conjunction)",
            "感動詞 (Interjection)", "連体詞 (Pre-noun adjectival)",
            "助動詞 (Auxiliary verb)"
         ],
         "countries": [
            "Japan"
         ]
      },
      "Chinese (Mandarin)": {
         "flag": "flags/Chinese.webp",
         "pos": [
            "名词 (Noun)", "动词 (Verb)", "形容词 (Adjective)",
            "副词 (Adverb)", "代词 (Pronoun)", "介词 (Preposition)",
            "连词 (Conjunction)", "助词 (Particle)", "叹词 (Interjection)",
            "量词 (Measure word)"
         ],
         "countries": [
            "China", "Taiwan", "Singapore"
         ]
      },
      "Korean": {
         "flag": "flags/Korean.webp",
         "pos": [
            "명사 (Noun)", "동사 (Verb)", "형용사 (Adjective)",
            "부사 (Adverb)", "대명사 (Pronoun)", "조사 (Particle)",
            "접속사 (Conjunction)", "감탄사 (Interjection)", "관형사 (Determiner)"
         ],
         "countries": [
            "South Korea", "North Korea"
         ]
      },
      "Arabic": {
         "flag": "flags/Arabic.webp",
         "pos": [
            "اسم (Noun)", "فعل (Verb)", "صفة (Adjective)",
            "ظرف (Adverb)", "حرف جر (Preposition)", "حرف عطف (Conjunction)",
            "حرف نداء (Interjection)", "ضمير (Pronoun)"
         ],
         "countries": [
            "Egypt", "Saudi Arabia", "Iraq", "Morocco", "Algeria",
            "Sudan", "Yemen", "Syria", "Jordan", "Tunisia",
            "Libya", "Lebanon", "Kuwait", "Oman", "Qatar",
            "United Arab Emirates"
         ]
      },
      "Turkish": {
         "flag": "flags/Turkish.webp",
         "pos": [
            "İsim", "Fiil", "Sıfat", "Zarf", "Zamir",
            "Edat (Postposition)", "Bağlaç", "Ünlem"
         ],
         "countries": [
            "Turkey", "Cyprus"
         ]
      },
      "Thai": {
         "flag": "flags/Thai.webp",
         "pos": [
            "คำนาม (Noun)", "คำกริยา (Verb)", "คำคุณศัพท์ (Adjective)",
            "คำกริยาวิเศษณ์ (Adverb)", "คำสรรพนาม (Pronoun)",
            "คำบุพบท (Preposition)", "คำสันธาน (Conjunction)",
            "คำอุทาน (Interjection)", "คำลักษณะนาม (Classifier)"
         ],
         "countries": [
            "Thailand"
         ]
      },
   }

   for lang_name, data in LANGUAGES_DATA.items():
      language, created = Language.objects.get_or_create(name=lang_name)
      if not language.image:
         flag_path = data["flag"]
         
         full_path = os.path.join(settings.MEDIA_ROOT, flag_path)
         if os.path.isfile(full_path):
            img = Image.objects.create(file=flag_path)
            language.image = img
            language.save(update_fields=['image'])
      
      for pos_name in data["pos"]:
         PartOfSpeech.objects.get_or_create(name=pos_name, language=language)

      for country_name in data["countries"]:
         try:
            country = Country.objects.get(name=country_name)
            CountryLanguage.objects.get_or_create(language=language, country=country)
         except Country.DoesNotExist:
            pass