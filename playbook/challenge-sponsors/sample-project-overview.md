# Cal Poly AI Innovation Projects

## Project 1: Math Placement AI Assistant

### Project Overview

This project aims to develop an AI-powered chatbot to assist Cal Poly students with math placement questions and reduce the workload on academic staff. The system will provide conversational support for students navigating the complex math placement process, answering frequently asked questions, and potentially integrating with student records to provide personalized guidance. Currently, one staff member (Clint) handles approximately 750+ email exchanges and numerous phone calls from anxious students seeking clarification about their math placement.

### Project Objectives

- Create an AI agent that can answer math placement questions conversationally
- Reduce email volume and phone calls to the Math Placement Coordinator
- Provide immediate responses to student inquiries (currently 5-day backlog)
- Decrease student anxiety through patient, available guidance
- Support both prospective and admitted students with placement information
- Potentially integrate with Slate CRM and student information systems for personalized responses

### Current Workflow

1. **Student Admission (Early April)**: Students are admitted and receive math placement survey on their to-do list
2. **Information Exchange**: Survey collects official placement data and asks students about additional credentials (AP scores, SAT scores, community college courses)
3. **Provisional Placement**: System provides initial placement based on major requirements and available data
4. **Action Plan Generation**: Students receive customized action plans with options like:
   - Send official scores by July 15th
   - Take placement exam (online, summer course, or in-person)
   - Do nothing (start in prerequisite course)
   - Complete math requirements (no action needed)
5. **Student Questions Begin**: Flood of emails and phone calls seeking clarification

### Key Pain Points

- **Volume Overload**: 750+ email exchanges for ~5,500 incoming students handled by one person
- **Repetitive Questions**: Same questions asked repeatedly (e.g., "Doesn't my high school precalculus count?")
- **Student Anxiety**: High stress levels about placement and flow chart progression
- **Response Delays**: 5-day backlog creating frustrated students and follow-up emails
- **Manual Process**: Staff member manually answers each inquiry despite having FAQ pages
- **Verification Issues**: Students question the accuracy of official policy statements

### Ideal Solution Vision

**Phase 1 (Summer Prototype)**: Public-facing AI agent that can answer general math placement questions for any prospective Cal Poly student using algorithmic placement rules and FAQ information.

**Phase 2 (Future Implementation)**: Integrated AI agent connected to Slate CRM and student information systems that can:

- Access individual student records
- Provide personalized placement information
- Have dynamic conversations about specific student situations
- Update student records or tracking information
- Operate within Cal Poly's secure ecosystem with proper FERPA compliance

### Data Availability

- **Math Placement Algorithm**: Well-defined, completely algorithmic placement criteria
- **FAQ Documentation**: Existing web pages with placement policies and procedures
- **Email Samples**: 750+ student email exchanges (require anonymization)
- **Survey Data**: Student responses and placement information from Slate
- **Anonymized Student Records**: Sample data with placement-relevant fields
- **Workflow Documentation**: Process flows and decision trees
- **Test Data**: Potential access to Slate test database with dummy student profiles

### Technical Considerations

- **Slate API Integration**: Possible but requires security review for student data access
- **FERPA Compliance**: Student record access requires secure implementation
- **Single Sign-On**: Future integration would need Cal Poly authentication
- **Scalability**: Solution should handle 5,500+ students annually

---

## Project 2: Course Articulation AI System

### Project Overview

This project would develop an AI system to assist with course articulation between educational institutions, helping students and advisors understand how credits transfer between schools. The system would need to handle the complex, non-transitive nature of course equivalencies while providing accurate guidance for transfer students.

### Project Objectives

- Automate course articulation analysis and recommendations
- Handle complex multi-institution transfer scenarios
- Provide guidance for students transferring between community colleges, CSUs, and other institutions
- Support advisors in making transfer credit decisions
- Integrate with existing articulation databases like ASSIST.org

### Current Workflow

- Manual review of course descriptions and syllabi
- Reference to ASSIST.org database for California community college transfers
- Individual advisor consultations for complex cases
- Time-intensive research for non-standard articulations

### Key Pain Points

- **Non-Transitive Relationships**: Course A = Course B and Course B = Course C does not mean Course A = Course C
- **Data Normalization**: Different institutions use varying course numbering and description formats
- **Complex Decision Making**: Requires human judgment for edge cases
- **Time-Intensive Process**: Manual review of transfer credits creates bottlenecks

### Ideal Solution Vision

An AI system that can analyze course descriptions, learning outcomes, and institutional standards to provide articulation recommendations while acknowledging the limitations of transitive relationships in course equivalency.

### Data Availability

- **ASSIST.org Database**: California community college articulation agreements
- **Course Catalogs**: Publicly available from various institutions
- **Transfer Credit Histories**: Historical articulation decisions (anonymized)
- **Institutional Standards**: Degree requirements and course prerequisites

### Technical Considerations

- **Data Integration**: Normalizing course data across multiple institution formats
- **Accuracy Requirements**: High stakes for student academic progress
- **Human Oversight**: System should augment rather than replace human decision-making
- **Existing Competition**: Other research groups already working on similar AI articulation projects
