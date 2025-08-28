<?php
namespace local_aigrader;

defined('MOODLE_INTERNAL') || die();

class observer {

    public static function catch_all_events(\mod_quiz\event\attempt_reviewed $event) {
        global $DB;

        $quiz_attempt_id = $event->objectid;
        if (empty($quiz_attempt_id)) {
            return;
        }

        try {
            $attempt_obj = $DB->get_record('quiz_attempts', ['id' => $quiz_attempt_id]);
            if (!$attempt_obj) {
                return;
            }
            $questionusageid = $attempt_obj->uniqueid;
            $question_attempts = $DB->get_records('question_attempts', ['questionusageid' => $questionusageid]);

            if (empty($question_attempts)) {
                return;
            }
            
            $error_messages = [];

            foreach ($question_attempts as $qa) {
                $question = $DB->get_record('question', ['id' => $qa->questionid]);

                if ($question && $question->qtype == 'essay') {
                    $user_answer = '';
                    $sql = "SELECT d.value
                              FROM {question_attempt_step_data} d
                              JOIN {question_attempt_steps} s ON s.id = d.attemptstepid
                             WHERE s.questionattemptid = :qaid AND d.name = 'answer'
                          ORDER BY s.id DESC";
                    $params = ['qaid' => $qa->id];
                    
                    $answer_value = $DB->get_field_sql($sql, $params, 0, 1);

                    if ($answer_value !== false) {
                        $user_answer = $answer_value;
                    }

                    $result = self::call_ai_analyzer($question, $user_answer);

                    if (is_array($result)) {
                        $single_report_html = self::format_analysis_report($result);
                        $notification_title = "<h2><span class='fa fa-lightbulb-o'></span> AI Analiza (NIJE SAČUVANO)</h2>";
                        \core\notification::add($notification_title . $single_report_html, \core\notification::SUCCESS);
                    } else {
                        $error_messages[] = "<b>Pitanje '" . htmlspecialchars($question->name) . "':</b> " . $result;
                    }
                }
            }

            if (!empty($error_messages)) {
                $error_string = "<h2><span class='fa fa-exclamation-triangle text-danger'></span> Greške prilikom AI analize</h2><ul>";
                foreach ($error_messages as $err) { $error_string .= "<li>" . $err . "</li>"; }
                $error_string .= "</ul>";
                \core\notification::add($error_string, \core\notification::ERROR);
            }

        } catch (\Exception $e) {
            \core\notification::add("AI Grader: Kritična greška: " . $e->getMessage(), \core\notification::ERROR);
        }
    }

    // =========================================================================
    // === FUNKCIJA ZA POZIV API-ja (uglavnom ista, samo provera ključa) ===
    // =========================================================================
    private static function call_ai_analyzer(object $question, string $user_answer) {
        $api_url = "http://127.0.0.1:8000/proveri-odgovor";
        $question_text = strip_tags($question->questiontext);

        if (empty(trim($user_answer))) {
            return [ "info_only" => "Student nije dao odgovor.", "originalno_pitanje" => $question_text, "odgovor_studenta" => "(prazno)" ];
        }

        $payload = ["pitanje" => $question_text, "odgovor" => $user_answer];
        $ch = curl_init($api_url);
        curl_setopt_array($ch, [ CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_POSTFIELDS => json_encode($payload), CURLOPT_HTTPHEADER => ['Content-Type: application/json'], CURLOPT_TIMEOUT => 180, ]);
        $response_body = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curl_error = curl_error($ch);
        curl_close($ch);
        if ($curl_error) return "Greška pri konekciji sa AI serverom: {$curl_error}.";
        if ($http_code !== 200) return "AI server je vratio grešku (HTTP status: {$http_code}). Odgovor: <pre>" . htmlspecialchars($response_body) . "</pre>";
        
        $data = json_decode($response_body, true);
        if (json_last_error() !== JSON_ERROR_NONE) return "Greška: Odgovor od AI servera nije validan JSON.";

        // Proveravamo ključ 'ocena_numericka' koji je na vrhu finalnog JSON-a.
        if (!isset($data['ocena_numericka'])) {
             return "Greška: AI odgovor ne sadrži ključ 'ocena_numericka'.";
        }
        
        $data['originalno_pitanje'] = $question_text;
        $data['odgovor_studenta'] = $user_answer;
        return $data;
    }
    
    // =========================================================================
    // === AŽURIRANA FUNKCIJA za formatiranje HTML izveštaja (najveća promena) ===
    // =========================================================================
    private static function format_analysis_report(array $result): string {
        $html = "<div style='border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; background-color: #f9f9f9;'>";
        $html .= "<h4>Evaluacija za pitanje: \"" . htmlspecialchars($result['originalno_pitanje']) . "\"</h4>";
        $html .= "<p><strong>Odgovor studenta:</strong> " . nl2br(htmlspecialchars($result['odgovor_studenta'])) . "</p>";

        if (isset($result['info_only'])) {
             $html .= "<p><strong>Info:</strong> " . htmlspecialchars($result['info_only']) . "</p></div>";
             return $html;
        }

        $html .= "<hr>";

        // Pristupamo podacima direktno iz $result niza.
        $ocena_numericka = $result['ocena_numericka'] ?? 'N/A';
        $rezime_evaluacije = $result['rezime_evaluacije'] ?? 'Nema rezimea.';
        
        // Prikazujemo ocenu u formatu X/5.
        $html .= "<p style='font-size: 1.2em; font-weight: bold; color: #0056b3;'>Predlog ocene: " . htmlspecialchars($ocena_numericka) . " / 5</p>";
        
        // Prikazujemo detaljan rezime koji sada sadrži sve bitne informacije.
        $html .= "<div style='margin-top: 10px; padding: 10px; background-color: #e9ecef; border-radius: 4px;'><strong>Rezime evaluacije:</strong><br>" . nl2br(htmlspecialchars($rezime_evaluacije)) . "</div>";
        
        // Opciono: Ako API vraća i analizu po kriterijumima, možemo je prikazati.
        // Ovo je dodato kao bonus, ako vaš finalni prompt to podržava. Ako ne, ovaj deo se neće prikazati.
        $analiza_kriterijuma = $result['analiza_kriterijuma'] ?? [];
        if (!empty($analiza_kriterijuma)) {
            $html .= "<div style='margin-top: 15px;'>";
            $html .= "<h4>Analiza po ključnim tačkama:</h4>";
            $html .= "<ul style='list-style-type: disc; padding-left: 20px;'>";
            foreach ($analiza_kriterijuma as $stavka) {
                $kriterijum = htmlspecialchars($stavka['kriterijum'] ?? 'Nepoznat kriterijum');
                $zapažanje = htmlspecialchars($stavka['zapažanje'] ?? 'Nema zapažanja.');
                $html .= "<li style='margin-bottom: 8px;'><strong>{$kriterijum}:</strong> {$zapažanje}</li>";
            }
            $html .= "</ul></div>";
        }

        // Prikaz celog JSON-a za debagovanje ostaje koristan.
        $html .= "<details style='margin-top: 15px;'>";
        $html .= "<summary style='cursor: pointer; color: #0056b3; font-weight: bold;'>Prikaži/sakrij tehničke detalje (ceo JSON odgovor)</summary>";
        $html .= "<pre style='background-color: #333; color: #f8f8f2; border: 1px solid #ccc; padding: 10px; white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto; margin-top: 5px; border-radius: 4px;'>" . htmlspecialchars(json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) . "</pre>";
        $html .= "</details>";
        $html .= "</div>";
        return $html;
    }
}