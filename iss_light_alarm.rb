require 'hue'
require 'json'
require 'net/http'
require 'rufus-scheduler'
require 'uri'
require 'yaml'

class IssAlarmLight
  Version = '0.0.1'
  OPEN_NOTIFY_API_URL = "http://api.open-notify.org/iss-pass.json"

  def initialize(arguments, stdin)
    # Configuration file is ".iss_light_alarm.yaml" in this directory
    configuration = YAML.load_file(File.join(__dir__, 'iss_light_alarm.yaml'))
    @latitude = configuration['location']['latitude']
    @longitude = configuration['location']['longitude']
    
    @Client = Hue::Client.new
    @light = @Client.lights[3]
    @sched = Rufus::Scheduler.new
  end
  
  ##
  # Turn the lights on at the start of the overflight
  # and then turn the lights back off at the end
  def run_light_sequence(duration)
    @light.set_state( { :on => true })
    @sched.in duration do
      @light.set_state( { :on => false })
    end
    @sched.in duration do
      request_pass_update
    end
  end

  ##
  # Get the next time the ISS will be above 10 degrees of elevation as observed
  # from the coordinates provided
  #
  def request_pass_update
    uri = URI.parse("#{OPEN_NOTIFY_API_URL}?lat=#{@latitude}&lon=#{@longitude}")
    response = Net::HTTP.get_response(uri)
    open_notify_response = JSON.parse(response.body)
    if open_notify_response['message'] == "success"
      # The "respsonse" section contains an array of risetime & duration elements, we just want the first
      next_risetime = open_notify_response['response'][0]['risetime']
      next_duration = open_notify_response['response'][0]['duration']

      # This is in gmt but for consistency should be local time
      puts "next risetime is #{DateTime.strptime(next_risetime.to_s, '%s')}"
      puts "and will last for #{next_duration} seconds"
      # so we should schedule our next check for next_risetime + next_duration (seconds)
      @sched.at next_risetime do
         run_light_sequence next_duration
      end
    else
      puts "error response from api: "
      puts response.body
    end
    @sched.join
  end
end

if __FILE__ == $0 then
  issalarm = IssAlarmLight.new(ARGV, STDIN)
  issalarm.request_pass_update
end
