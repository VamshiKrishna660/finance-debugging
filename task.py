## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, FinancialDocumentTool

## Creating a task to help solve user's query
analyze_financial_document = Task(
    description="""Thoroughly analyze the financial document located at: {file_path} to answer the user's query: {query}
    
    Your analysis should include:
    1. Extract and analyze key financial metrics (revenue, profit margins, cash flow, debt ratios, etc.)
    2. Identify significant trends and patterns in the financial data
    3. Evaluate the overall financial health and performance
    4. Assess any notable strengths or weaknesses in the financials
    5. Provide context by comparing to industry benchmarks where relevant
    6. Search for recent market news or developments related to the company/sector if applicable
    
    Be thorough, accurate, and base all conclusions on the actual data in the document.
    """,

    expected_output="""A comprehensive financial analysis report including:
    - Executive summary of key findings
    - Detailed breakdown of important financial metrics and ratios
    - Trend analysis with specific data points
    - Assessment of financial health and performance
    - Identification of any red flags or notable strengths
    - Market context and relevant industry comparisons
    - Clear, data-driven conclusions addressing the user's query
    
    All analysis must be based on factual data from the document with proper citations.
    """,

    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    async_execution=False,
)

## Creating a document verification task
document_verification = Task(
    description="""Verify the financial document located at: {file_path} for completeness, authenticity, and data quality.
    
    Your verification should include:
    1. Confirm the document is indeed a financial document (balance sheet, income statement, cash flow, etc.)
    2. Check for completeness of required financial sections
    3. Verify data consistency across different parts of the document
    4. Identify any missing critical information
    5. Flag any unusual patterns or potential data quality issues
    6. Confirm compliance with standard financial reporting formats
    
    Provide a clear verification status and highlight any concerns.
    """,

    expected_output="""A verification report including:
    - Document type confirmation
    - Completeness assessment
    - Data consistency check results
    - List of any missing critical information
    - Data quality assessment
    - Overall verification status (Verified/Verified with concerns/Failed verification)
    - Specific recommendations for any issues found
    """,

    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description="""Based on the financial analysis, provide prudent investment recommendations.
    
    Your analysis should consider:
    1. The user's query and investment objectives: {query}
    2. Financial health indicators from the document
    3. Growth potential and sustainability
    4. Market conditions and sector outlook
    5. Risk factors and potential concerns
    6. Alignment with different investor profiles (conservative, moderate, aggressive)
    
    Provide balanced, evidence-based investment guidance with appropriate disclaimers.
    """,

    expected_output="""A professional investment recommendation report including:
    - Investment thesis based on financial analysis
    - Suitable investor profiles for this opportunity
    - Potential return expectations with realistic assumptions
    - Time horizon recommendations
    - Diversification considerations
    - Key factors to monitor going forward
    - Important risk disclaimers and regulatory compliance notes
    
    All recommendations must be based on factual analysis with clear reasoning.
    """,

    agent=investment_advisor,
    tools=[search_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description="""Conduct a comprehensive risk assessment of the investment opportunity.
    
    Your assessment should analyze:
    1. Financial risks (liquidity, solvency, profitability concerns)
    2. Market risks (sector volatility, economic sensitivity)
    3. Operational risks (business model sustainability, competitive position)
    4. Regulatory and compliance risks
    5. Risk-reward balance for different scenarios
    6. Risk mitigation strategies
    
    Provide objective, balanced risk analysis with quantifiable metrics where possible.
    """,

    expected_output="""A detailed risk assessment report including:
    - Overall risk rating (Low/Medium/High) with justification
    - Breakdown of specific risk categories with severity levels
    - Key risk indicators and their current status
    - Scenario analysis (best case, base case, worst case)
    - Risk mitigation recommendations
    - Stress test considerations
    - Ongoing risk monitoring suggestions
    
    All risk assessments must be data-driven and objectively justified.
    """,

    agent=risk_assessor,
    tools=[search_tool],
    async_execution=False,
)