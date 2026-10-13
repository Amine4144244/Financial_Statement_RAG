import pymupdf


def generate_apple_report():
    doc = pymupdf.open()

    # Page 1: Cover & Business Overview
    p1 = doc.new_page()
    p1.insert_text((50, 60), "UNITED STATES SECURITIES AND EXCHANGE COMMISSION", fontsize=10)
    p1.insert_text((50, 75), "Washington, D.C. 20549", fontsize=9)
    p1.insert_text((50, 100), "FORM 10-K", fontsize=18)
    p1.insert_text((50, 130), "ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934", fontsize=9)
    p1.insert_text((50, 155), "For the Fiscal Year Ended September 28, 2024", fontsize=13)
    p1.insert_text((50, 190), "APPLE INC.", fontsize=16)
    p1.insert_text((50, 210), "One Apple Park Way, Cupertino, California 95014", fontsize=10)
    p1.insert_text((50, 230), "Trading Symbol: AAPL (Nasdaq Global Select Market)", fontsize=10)

    p1.insert_text((50, 270), "PART I", fontsize=12)
    p1.insert_text((50, 290), "Item 1. Business", fontsize=12)
    business_text = """Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a variety of related services. The Company's fiscal year is the 52- or 53-week period that ends on the last Saturday of September.

Product categories include iPhone, Mac, iPad, and Wearables, Home and Accessories. Services includes Advertising, AppleCare, Cloud Services, Digital Content and Payment Services."""
    p1.insert_textbox(pymupdf.Rect(50, 310, 550, 750), business_text, fontsize=10)

    # Page 2: Risk Factors
    p2 = doc.new_page()
    p2.insert_text((50, 60), "Item 1A. Risk Factors", fontsize=14)
    risk_text = """Our business, results of operations, and financial condition are subject to various risks:

- Global Supply Chain & Component Sourcing: The Company relies on single-source or limited-source suppliers for multiple critical components, and disruptions may impact device availability.
- Intense Market Competition: Technological changes in mobile devices, services, and artificial intelligence present ongoing competitive dynamics.
- Foreign Exchange Rate Fluctuations: With significant international sales, currency volatility against the U.S. Dollar creates margin variances."""
    p2.insert_textbox(pymupdf.Rect(50, 85, 550, 650), risk_text, fontsize=10)

    # Page 3: MD&A
    p3 = doc.new_page()
    p3.insert_text((50, 60), "PART II", fontsize=12)
    p3.insert_text((50, 80), "Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations", fontsize=12)
    mda_text = """Executive Overview

During fiscal year 2024, total net sales reached $391,035 million, representing a 2.0% increase compared to $383,285 million in fiscal year 2023. Gross margin increased to $180,683 million (46.2% of net sales) driven by Services revenue growth and favorable product mix.

Operating income expanded to $123,263 million, up 7.8% from $114,301 million in fiscal 2023. Net income was $93,295 million compared to $96,178 million in the prior year, reflecting higher tax provisions."""
    p3.insert_textbox(pymupdf.Rect(50, 105, 550, 650), mda_text, fontsize=10)

    # Page 4: Financial Statements - Income Statement
    p4 = doc.new_page()
    p4.insert_text((50, 60), "Consolidated Statements of Operations", fontsize=14)
    p4.insert_text((50, 80), "(In millions, except number of shares and per share amounts)", fontsize=9)
    table_text = """Years ended September 28, 2024 and September 30, 2023        2024          2023

Revenue                                                   $391,035      $383,285
Cost of sales                                              210,352       214,137
Gross profit                                               180,683       169,148

Operating expenses:
  Research and development                                  31,370        29,915
  Selling, general and administrative                       26,050        24,932
Total operating expenses                                    57,420        54,847

Operating income                                           123,263       114,301
Other income, net                                              240          (382)
Income before taxes                                        123,503       113,919
Provision for income taxes                                  30,208        16,741
Net income                                                 $93,295       $96,178"""
    p4.insert_textbox(pymupdf.Rect(50, 105, 550, 650), table_text, fontsize=10)

    doc.save("apple_annual_report_2024.pdf")
    doc.close()
    print("Generated apple_annual_report_2024.pdf successfully.")


def generate_microsoft_report():
    doc = pymupdf.open()

    # Page 1: Cover & Business Overview
    p1 = doc.new_page()
    p1.insert_text((50, 60), "UNITED STATES SECURITIES AND EXCHANGE COMMISSION", fontsize=10)
    p1.insert_text((50, 75), "Washington, D.C. 20549", fontsize=9)
    p1.insert_text((50, 100), "FORM 10-K", fontsize=18)
    p1.insert_text((50, 130), "ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934", fontsize=9)
    p1.insert_text((50, 155), "For the Fiscal Year Ended June 30, 2024", fontsize=13)
    p1.insert_text((50, 190), "MICROSOFT CORPORATION", fontsize=16)
    p1.insert_text((50, 210), "One Microsoft Way, Redmond, Washington 98052-6399", fontsize=10)
    p1.insert_text((50, 230), "Trading Symbol: MSFT (Nasdaq Global Select Market)", fontsize=10)

    p1.insert_text((50, 270), "PART I", fontsize=12)
    p1.insert_text((50, 290), "Item 1. Business", fontsize=12)
    business_text = """Microsoft Corporation develops and supports software, services, devices, and solutions that deliver new value for customers and help businesses realize their full potential.

Our operations are organized into three segments:
1. Productivity and Business Processes (Office, LinkedIn, Dynamics)
2. Intelligent Cloud (Azure, Windows Server, GitHub)
3. More Personal Computing (Windows, Devices, Xbox and gaming)"""
    p1.insert_textbox(pymupdf.Rect(50, 310, 550, 750), business_text, fontsize=10)

    # Page 2: Risk Factors
    p2 = doc.new_page()
    p2.insert_text((50, 60), "Item 1A. Risk Factors", fontsize=14)
    risk_text = """Our operations are subject to diverse risks:
- Intense Competition in Cloud & Artificial Intelligence.
- Cybersecurity and cloud tenant data protection.
- Large capital expenditures for AI datacenters."""
    p2.insert_textbox(pymupdf.Rect(50, 85, 550, 650), risk_text, fontsize=10)

    # Page 3: MD&A
    p3 = doc.new_page()
    p3.insert_text((50, 60), "PART II", fontsize=12)
    p3.insert_text((50, 80), "Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations", fontsize=12)
    mda_text = """Executive Overview

Fiscal year 2024 was marked by strong commercial cloud momentum and operational discipline. Total revenue grew to $245,122 million, representing a 15.7% increase compared to fiscal year 2023 ($211,915 million).

Operating income increased 23.9% to $109,640 million, driven by operating leverage in Intelligent Cloud."""
    p3.insert_textbox(pymupdf.Rect(50, 105, 550, 650), mda_text, fontsize=10)

    # Page 4: Financial Statements - Income Statement
    p4 = doc.new_page()
    p4.insert_text((50, 60), "Consolidated Statements of Income", fontsize=14)
    p4.insert_text((50, 80), "(In millions, except per share amounts)", fontsize=9)
    table_text = """For the Fiscal Year Ended June 30,                             2024          2023

Revenue                                                   $245,122      $211,915
Cost of revenue                                             74,102        65,863
Gross profit                                               171,020       146,052

Operating expenses:
  Research and development                                  29,510        27,195
  Sales and marketing                                       24,420        22,759
  General and administrative                                 7,450         7,575
Total operating expenses                                    61,380        57,529

Operating income                                           109,640        88,523
Other income, net                                            2,340         1,025
Income before income taxes                                 111,980        89,548
Provision for income taxes                                  23,844        17,187
Net income                                                 $88,136       $72,361"""
    p4.insert_textbox(pymupdf.Rect(50, 105, 550, 650), table_text, fontsize=10)

    doc.save("microsoft_annual_report_2024.pdf")
    doc.close()
    print("Generated microsoft_annual_report_2024.pdf successfully.")


if __name__ == "__main__":
    generate_apple_report()
    generate_microsoft_report()
