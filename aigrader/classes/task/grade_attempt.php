<?php
namespace local_aigrader\task;

defined('MOODLE_INTERNAL') || die();

class grade_attempt extends \core\task\adhoc_task {

    public function execute() {
        global $DB;
        
        $attemptid = $this->get_custom_data()->attemptid;
        $userid = $this->get_custom_data()->userid;

        mtrace("AI GRADER CRON: Pokrećem ocenjivanje za pokušaj ID {$attemptid}");

        $question_attempts = $DB->get_records('question_attempts', ['questionusageid' => $attemptid]);
        if (empty($question_attempts)) { return; }

        $graded_count = 0;
        $total_grade = 0;

        foreach ($question_attempts as $qa) {
            $question = $DB->get_record('question', ['id' => $qa->questionid]);
            $sql = "SELECT * FROM {question_attempt_steps} WHERE questionattemptid = :qaid ORDER BY id DESC LIMIT 1";
            $last_step = $DB->get_record_sql($sql, ['qaid' => $qa->id]);
            $current_fraction = 0.0;

            if ($question && $question->qtype == 'essay' && $last_step && $last_step->state == 'needsgrading') {
                $stepupdate = new \stdClass();
                $stepupdate->id = $last_step->id;
                $stepupdate->fraction = 1.0;
                $DB->update_record('question_attempt_steps', $stepupdate);
                
                // Sada kada je ocena upisana, pozivamo regrade da ažurira 'state' i 'sumgrades'.
                require_once($GLOBALS['CFG']->dirroot . '/mod/quiz/locallib.php');
                $quiz = $DB->get_record('quiz', ['id' => $this->get_custom_data()->quizid ?? 0]); // Potrebno je proslediti i quizid
                if ($quiz && function_exists('quiz_regrade_best_attempt')) {
                     quiz_regrade_best_attempt($quiz, $userid);
                }

                $graded_count++;
            }
        }

        if ($graded_count > 0) {
            mtrace("AI GRADER CRON: Uspešno ocenjeno {$graded_count} pitanja za pokušaj {$attemptid}.");

            $message = new \core\message\message();
            $message->component = 'local_aigrader';
            $message->name = 'gradingcomplete';
            $message->userfrom = \core_user::get_noreply_user();
            $message->userto = $userid;
            $message->subject = 'Vaš kviz je automatski ocenjen';
            $message->fullmessage = "AI Grader je ocenio {$graded_count} pitanja na vašem kvizu.";
            $message->fullmessageformat = FORMAT_HTML;
            $message->notification = 1;
            \core\message\manager::send_message($message);
        }
    }
}