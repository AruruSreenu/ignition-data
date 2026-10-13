SELECT
    Title,
    Description,
    FeedbackType,
    Priority,
    Status,
    ModuleName,
    CreatedBy,
    CreatedDate
FROM SoftwareFeedback
ORDER BY CreatedDate DESC;