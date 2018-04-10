import os
from sqlalchemy import create_engine

from datapackage_pipelines.wrapper import process

engine = create_engine(os.environ['DPP_DB_ENGINE'])

UNREPORTED_TURNOVER_ASSOCIATIONS_QUERY = """
SELECT count(1) as count
FROM guidestar_processed
WHERE association_field_of_activity='{foa}'
  AND (association_yearly_turnover = 0
       OR association_yearly_turnover IS NULL)
"""

REPORTED_TURNOVER_ASSOCIATIONS_QUERY = """
SELECT id,
       association_title AS name,
       association_yearly_turnover AS amount
FROM guidestar_processed
WHERE association_field_of_activity='{foa}'
  AND association_yearly_turnover > 0
ORDER BY 3 DESC
"""

unreported_turnover_associations_ = {}
def unreported_turnover_associations(foa):
    if unreported_turnover_associations_.get(foa) is None:
        query = UNREPORTED_TURNOVER_ASSOCIATIONS_QUERY.format(foa=foa)
        results = engine.execute(query)
        unreported_turnover_associations_[foa] = int(dict(list(results)[0])['count'])

    return unreported_turnover_associations_[foa]


reported_turnover_associations_ = {}
def reported_turnover_associations(foa):
    if reported_turnover_associations_.get(foa) is None:
        query = REPORTED_TURNOVER_ASSOCIATIONS_QUERY.format(foa=foa)
        results = engine.execute(query)
        reported_turnover_associations_[foa] = [dict(r) for r in results]

    return reported_turnover_associations_[foa]
    

def process_row(row, *_):
    if row['kind'] == 'association':
        id = row['id']
        foa = row['details']['field_of_activity']
        foad = row['details']['field_of_activity_display']
        num_of_employees = row['details']['num_of_employees']
        num_of_volunteers = row['details']['num_of_volunteers']
        last_report_year = row['details']['last_report_year']
        num_unreported = unreported_turnover_associations(foa)
        reported_list = reported_turnover_associations(foa)
        selected_index = [i for i, x in enumerate(reported_list) if x['id'] == row['id']]
        if len(selected_index) > 0:
            selected_index = selected_index[0]
        else:
            selected_index = None
        salaries = row['details']['top_salaries']
        if salaries:
            top_salary = salaries[0]['salary']
        else:
            top_salary = None
        median_turnover_in_field_of_activity = row['details']['median_turnover_in_field_of_activity']
        charts = []
        charts.append({
                'title': 'מיהו הארגון?',
                'long_title': 'מיהו הארגון',
                'type': 'template',
                'template_id': 'org_status'
        })
        charts.append({
                'title': 'מקבל כספי ממשלה?',
                'long_title': 'האם הארגון מקבל כספי ממשלה?',
                'description': 'התקשרויות ותמיכות לפי משרדים, הנתונים כוללים העברות המתועדות במקורות המידע הזמינים מכל השנים.',
        })
        charts.append({
                'title': 'אילו אישורים?',
                'long_title': 'אישורים והכרה בארגון',
                'type': 'template',
                'template_id': 'org_credentials'
        })
        if None not in (last_report_year, 
                        num_of_employees, 
                        num_of_volunteers, 
                        top_salary, 
                        median_turnover_in_field_of_activity, 
                        foad):
            charts.append({
                'title': 'כמה עובדים ומתנדבים?',
                'long_title': 'כמה עובדים ומתנדבים בארגון',
                'type': 'vertical',
                'chart': {
                    'parts': [
                        {
                            'type': 'pointatron',
                            'title': 'מספר העובדים והמתנדבים בארגון בשנת {}'.format(last_report_year),
                            'chart': {
                                'values': [
                                    {
                                        'title': 'מספר עובדים',
                                        'amount': num_of_employees,
                                        'color': '#406025'
                                    },
                                    {
                                        'title': 'מספר מתנדבים',
                                        'amount': num_of_volunteers,
                                        'color': '#7FAA5E'
                                    },
                                ]
                            }
                        },
                        {
                            'type': 'comparatron',
                            'title': 'שכר השנתי הגבוה בארגון בשנת {}'.format(last_report_year),
                            'description': '*הנתונים מבוססים ומחושבים על בסיס המידע הזמין ומוצג ב<a href="http://www.guidestar.org.il/he/organization/{}" target="_blank">אתר גיידסטאר</a>'.format(id),
                            'chart': {
                                'main': {
                                    'amount': top_salary,
                                    'amount_fmt': '{:,} ₪'.format(top_salary),
                                    'label': 'מקבל השכר הגבוה בארגון'
                                },
                                'compare': {
                                    'amount': median_turnover_in_field_of_activity,
                                    'amount_fmt': '{:,} ₪'.format(median_turnover_in_field_of_activity),
                                    'label': 'חציון בתחום {}'.format(foad)
                                },

                            }
                        }
                    ]
                }
            })
        if foad is not None:
            charts.append({
                    'title': 'מי הארגונים הדומים?',
                    'long_title': 'ארגונים הפועלים בתחום {}, לפי גובה המחזור הכספי השנתי'.format(foad),
                    'description': '{} ארגונים נוספים הפועלים בתחום לא דיווחו על על גובה המחזור הכספי השנתי'
                                        .format(num_unreported),
                    'type': 'adamkey',
                    'chart': {
                        'values': [dict(
                            label='<a href="/i/org/association/{}">{}</a>'.format(x['id'], x['name']),
                            amount=x['amount'],
                            amount_fmt='{:,} ₪'.format(x['amount']),
                        )
                        for x in reported_list],
                        'selected': selected_index
                    }
            })
        row['charts'] = charts

    return row


def modify_datapackage(dp, *_):
    dp['resources'][0]['schema']['fields'].append(
        {
            'name': 'charts',
            'type': 'array',
            'es:itemType': 'object',
            'es:index': False
        }
    )
    return dp


if __name__ == '__main__':
    process(modify_datapackage=modify_datapackage,
            process_row=process_row)