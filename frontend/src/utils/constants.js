export const SLEEP_OPTIONS = [
  { value: 4.5, label: "Less than 5 hours (< 5 hrs)" },
  { value: 5.5, label: "5 to 6 hours" },
  { value: 6.5, label: "6 to 7 hours" },
  { value: 7.5, label: "7 to 8 hours" },
  { value: 8.5, label: "8 to 9 hours" },
  { value: 9.5, label: "More than 9 hours (> 9 hrs)" },
];

export const SLEEP_QUALITY_OPTIONS = [
  { value: 1, label: "1 — Very Poor", desc: "Restless, waking up exhausted" },
  { value: 2, label: "2 — Poor", desc: "Frequent awakenings, light sleep" },
  { value: 3, label: "3 — Average", desc: "Moderate sleep, occasional tiredness" },
  { value: 4, label: "4 — Good", desc: "Generally restful and undisturbed" },
  { value: 5, label: "5 — Excellent", desc: "Deep, fully restorative sleep" },
];

export const BEDTIME_OPTIONS = [
  { value: 1, label: "Before 11:00 PM" },
  { value: 2, label: "11:00 PM – 1:00 AM" },
  { value: 3, label: "1:00 AM – 3:00 AM" },
  { value: 4, label: "After 3:00 AM" },
];

export const SCREEN_OPTIONS = [
  { value: 1.0, label: "Less than 2 hours" },
  { value: 3.0, label: "2 to 4 hours" },
  { value: 5.0, label: "4 to 6 hours" },
  { value: 7.0, label: "6 to 8 hours" },
  { value: 9.0, label: "More than 8 hours" },
];

export const PHONE_BED_OPTIONS = [
  { value: 1, label: "Never", desc: "Keep device away before sleeping" },
  { value: 2, label: "Sometimes", desc: "Occasional browsing (1-2 nights/wk)" },
  { value: 3, label: "Usually", desc: "Most nights before falling asleep" },
  { value: 4, label: "Always", desc: "Every night directly until sleep" },
];

export const EXERCISE_OPTIONS = [
  { value: 0.0, label: "0 days (Sedentary)" },
  { value: 1.5, label: "1 to 2 days per week" },
  { value: 3.5, label: "3 to 4 days per week" },
  { value: 5.5, label: "5 or more days per week" },
];

export const DEADLINES_OPTIONS = [
  { value: 1, label: "0 to 2 upcoming deadlines (Low pressure)" },
  { value: 2, label: "3 to 5 deadlines (Moderate)" },
  { value: 3, label: "6 to 8 deadlines (Heavy)" },
  { value: 4, label: "9 or more deadlines (Extreme crunch)" },
];

export const WORKLOAD_OPTIONS = [
  { value: 1, label: "Very Light", desc: "Minimal academic pressure" },
  { value: 2, label: "Manageable", desc: "Reasonable study load" },
  { value: 3, label: "Heavy", desc: "Frequent stress and tight turnarounds" },
  { value: 4, label: "Overwhelming", desc: "Constant intense pressure" },
];

export const PERFORMANCE_OPTIONS = [
  { value: 1.0, label: "Much below expectations" },
  { value: 2.0, label: "Slightly below expectations" },
  { value: 3.0, label: "About as expected" },
  { value: 4.0, label: "Slightly above expectations" },
  { value: 5.0, label: "Much above expectations" },
  { value: null, label: "I have not taken any exams yet (No exam history)" },
];

export const PSS_OPTIONS = [
  { value: 1, label: "Never" },
  { value: 2, label: "Almost Never" },
  { value: 3, label: "Sometimes" },
  { value: 4, label: "Fairly Often" },
  { value: 5, label: "Very Often" },
];

export const DEFAULT_ASSESSMENT = {
  sleep_mid_hrs: 6.5,
  sleep_quality: 3,
  bedtime_code: 2,
  screen_mid_hrs: 5.0,
  phone_bed_code: 3,
  exercise_days_mid: 1.5,
  deadlines_code: 2,
  workload_code: 3,
  performance_code: 3.0,
  pss1_no_control: 3,
  pss2_confident: 3,
  pss3_going_my_way: 3,
  pss4_piling_up: 3,
};
