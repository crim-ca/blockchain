<%def name="get_style(field)">
    %if field in styles:
        ${styles[field]}
    %endif
</%def>

<%def name="get_styled_value(value, field=None)">
    %if value == "None" or value is None or str(value).lower() == "undefined":
        <span class="undefined">undefined</span>
    %elif field in styles:
        %if any(style in styles[field] for style in ["date", "datetime"]):
            <time datetime="${value}" class="${styles[field]}">${value.replace("T", " ")}</time>
        %else:
            <span class="${styles[field]}">${value}</span>
        %endif
    %else:
        <span>${value}</span>
    %endif
</%def>

<%def name="get_styled_change(change)">
    <div class="nowrap">
        [${get_styled_value(change["status"], "type")}]
        ${get_styled_value(" => ", "code")}
        %if change["status"] == "initial":
            ${get_styled_value(change["detail"], "undefined")}
        %elif change["action"] is None:
            ${change["detail"]}
        %else:
            ${get_styled_value(change["action"], "action")}
            ${get_styled_value(" [consent:", "plain")}
            ${get_styled_value(change["consent"], "bool")}
            ${get_styled_value("] from [", "plain")}
            ${get_styled_value(change["created"], "datetime")}
            %if change["expired"] is None:
                ${get_styled_value("] forever", "plain")}
            %else:
                ${get_styled_value("] until [", "plain")}
                ${get_styled_value(change["expired"], "datetime")}
                ${get_styled_value("]", "plain")}
            %endif
        %endif
    </div>
</%def>
