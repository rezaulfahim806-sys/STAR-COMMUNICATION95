package com.starcommunication.isp;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import androidx.core.app.NotificationCompat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

public class AutoMessageReceiver extends BroadcastReceiver {
    public static final String ACTION="com.starcommunication.isp.AUTO_MESSAGE";
    public static final String TYPE="type";
    public static final String PHONE="phone";
    public static final String NAME="name";

    @Override public void onReceive(Context context, Intent intent){
        String phone=intent.getStringExtra(PHONE); String name=intent.getStringExtra(NAME); String type=intent.getStringExtra(TYPE);
        if(phone==null||phone.trim().isEmpty())return;
        String msg;
        if("expiry".equals(type)) msg="প্রিয় "+(name==null?"Customer":name)+", আপনার ইন্টারনেট সংযোগের মেয়াদ শেষ হয়েছে। অনুগ্রহ করে বিল/রিনিউ করে সংযোগ চালু রাখুন। — STAR COMMUNICATION";
        else msg="প্রিয় "+(name==null?"Customer":name)+", নতুন মাসের ইন্টারনেট বিল শুরু হয়েছে। অনুগ্রহ করে সময়মতো বিল পরিশোধ করুন। — STAR COMMUNICATION";
        showReminder(context, name, msg, phone);
        if("month_end".equals(type)) scheduleMonthEnd(context,phone,name);
    }

    private static void showReminder(Context context,String name,String msg,String phone){
        NotificationManager nm=(NotificationManager)context.getSystemService(Context.NOTIFICATION_SERVICE);
        if(nm==null)return;
        String channel="star_customer_messages";
        if(android.os.Build.VERSION.SDK_INT>=26) nm.createNotificationChannel(new NotificationChannel(channel,"Customer Message Reminders",NotificationManager.IMPORTANCE_HIGH));
        Intent open=new Intent(context,MainActivity.class); open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi=PendingIntent.getActivity(context,(phone+msg).hashCode(),open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        NotificationCompat.Builder b=new NotificationCompat.Builder(context,channel)
                .setSmallIcon(R.drawable.star_launcher)
                .setContentTitle("STAR COMMUNICATION — Customer Message")
                .setContentText((name==null?"Customer":name)+" এর জন্য message reminder")
                .setStyle(new NotificationCompat.BigTextStyle().bigText(msg))
                .setAutoCancel(true).setContentIntent(pi);
        nm.notify((phone+msg).hashCode(),b.build());
    }

    public static void scheduleExpiry(Context c,String phone,String name,String expiry){
        try{
            Date d=new SimpleDateFormat("yyyy-MM-dd",Locale.US).parse(expiry);
            Calendar cal=Calendar.getInstance(); cal.setTime(d); cal.add(Calendar.DAY_OF_MONTH,1); cal.set(Calendar.HOUR_OF_DAY,9); cal.set(Calendar.MINUTE,0); cal.set(Calendar.SECOND,0); cal.set(Calendar.MILLISECOND,0);
            schedule(c,phone,name,"expiry",cal.getTimeInMillis());
        }catch(Exception ignored){}
    }
    public static void scheduleMonthEnd(Context c,String phone,String name){
        Calendar cal=Calendar.getInstance();
        cal.set(Calendar.DAY_OF_MONTH,1); cal.add(Calendar.MONTH,1); cal.add(Calendar.DAY_OF_MONTH,-1);
        cal.set(Calendar.HOUR_OF_DAY,20); cal.set(Calendar.MINUTE,0); cal.set(Calendar.SECOND,0); cal.set(Calendar.MILLISECOND,0);
        if(cal.getTimeInMillis()<=System.currentTimeMillis()){ cal.add(Calendar.MONTH,1); cal.set(Calendar.DAY_OF_MONTH,1); cal.add(Calendar.MONTH,-1); }
        schedule(c,phone,name,"month_end",cal.getTimeInMillis());
    }
    private static void schedule(Context c,String phone,String name,String type,long when){
        if(when<=System.currentTimeMillis())return;
        AlarmManager am=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE); if(am==null)return;
        Intent i=new Intent(c,AutoMessageReceiver.class); i.setAction(ACTION); i.putExtra(PHONE,phone); i.putExtra(NAME,name); i.putExtra(TYPE,type);
        int code=(phone+type).hashCode(); PendingIntent pi=PendingIntent.getBroadcast(c,code,i,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        try{if(android.os.Build.VERSION.SDK_INT>=23)am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,when,pi);else am.setExact(AlarmManager.RTC_WAKEUP,when,pi);}catch(Exception e){am.set(AlarmManager.RTC_WAKEUP,when,pi);}
    }
}
