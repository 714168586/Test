### 1、
    SELECT ci.id, ci.credit_no, ci.name, ci.card_no, ci.store_id, ci.saleman_id, ci.lawsuit_risk_summary, ci.lawsuit_risk_abstract, ci.unhealthy_info, ci.query_record, ci.created_at, ci.created_by, ci.updated_at, ci.updated_by, ci.remarks, ci.is_del, su.NAME AS SALESMAN_NAME, ts.STORE_NAME, ct.city AS CITY_NAME FROM credit_info ci LEFT JOIN SYSTEM_USER su ON ci.saleman_id = su.SYSTEM_ID LEFT JOIN tuodao_store ts ON ci.store_id = ts.STORE_ID LEFT JOIN cities ct ON ts.STORE_CITY = ct.cityid WHERE 1=1 ORDER BY ci.created_at DESC LIMIT 0,20


#### 优化思路：增加响应索引
	alter table credit_info add index IDX_CI_created_at(created_at)
	ALTER TABLE cities ADD INDEX IDX_CT_CID(cityid)
#### 加强制索引（这个在5.6.24版本中不需要强制，5.7.19需要使用强制索引）：
       SELECT ci.id, ci.credit_no, ci.name, ci.card_no, ci.store_id, ci.saleman_id, ci.lawsuit_risk_summary, ci.lawsuit_risk_abstract, ci.unhealthy_info, ci.query_record, ci.created_at, ci.created_by, ci.updated_at, ci.updated_by, ci.remarks, ci.is_del, su.NAME AS SALESMAN_NAME, ts.STORE_NAME, ct.city AS CITY_NAME FROM credit_info ci force index (IDX_CI_created_at) LEFT JOIN SYSTEM_USER su ON ci.saleman_id = su.SYSTEM_ID LEFT JOIN tuodao_store ts ON ci.store_id = ts.STORE_ID LEFT JOIN cities ct ON ts.STORE_CITY = ct.cityid WHERE 1=1 ORDER BY ci.created_at DESC LIMIT 0,20;

    现在已下降到0.1s

### 2、
    select count(0)
    from audit_info_history p1
    	left join loan_info_view p2 on p1.loan_id = p2.loan_id
    	left join tuodao_store p3 on p2.store_id = p3.store_id
    	left join cities p5 on p3.store_city = p5.cityid
    where 1 = 1
    
####  优化思路：增加响应索引
    ALTER TABLE audit_info_history ADD INDEX IDX_AIH_LOAN_ID(LOAN_ID)
    
    现在0.5s

### 3、
    SELECT COUNT(0)
    FROM credit_info ci
    	LEFT JOIN system_user su ON ci.saleman_id = su.SYSTEM_ID
    	LEFT JOIN tuodao_store ts ON ci.store_id = ts.STORE_ID
    	LEFT JOIN cities ct ON ts.STORE_CITY = ct.cityid
    WHERE 1 = 1 

#### 分析：
    tuodao_store store_id int 
    cities cityid varchar(20)
    类型不一样 索引不可用 所以cities cityid 转成int

#### 优化建议：
    ALTER TABLE cities MODIFY COLUMN cityid INT；
    优化后查询0.399s


### 5、
    SELECT
    			sum(IFNULL(IF((i.PRODUCT_TYPE=4||i.PRODUCT_TYPE=6||i.PRODUCT_TYPE=10||i.PRODUCT_TYPE=11),oli.OLD_LOAN_AMOUNT,i.LOAN_AMOUNT),0))  as LOAN_AMOUNT_SUM,
    			
    			sum(IF(sio.OVERDUE_ID>0,sio.REMIND_PRINCIPAL,rpn.CAPITAL)) AS PRINCIPAL_SUM,
    			IF((i.PRODUCT_TYPE=4||i.PRODUCT_TYPE=6||i.PRODUCT_TYPE=10||i.PRODUCT_TYPE=11),oli.OLD_LEND_TIME,i.LEND_TIME) AS LEND_TIME
    		FROM
          		repay_details i
    		LEFT JOIN repay_info r ON r.LOAN_ID = i.LOAN_ID
    		LEFT JOIN (SELECT SUM(PRINCIPAL) as CAPITAL,REPAY_ID from repay_plan WHERE STATUS in(1,3) GROUP BY REPAY_ID) rpn on rpn.REPAY_ID=i.REPAY_ID
    		LEFT JOIN old_loan_info oli ON oli.LOAN_ID=i.LOAN_ID
    		LEFT JOIN overdue_info ofo ON i.REPAY_ID=ofo.REPAY_ID
    		LEFT JOIN settle_info sio ON ofo.overdue_id=sio.OVERDUE_ID
    		WHERE 1=1
    		 
    	       AND IF((i.PRODUCT_TYPE=4||i.PRODUCT_TYPE=6||i.PRODUCT_TYPE=10||i.PRODUCT_TYPE=11),oli.OLD_LEND_TIME,i.LEND_TIME) >= DATE_FORMAT('2017-10-30', "%Y-%m-%d 00:00:00")
    	     
    		 
    	       AND IF((i.PRODUCT_TYPE=4||i.PRODUCT_TYPE=6||i.PRODUCT_TYPE=10||i.PRODUCT_TYPE=11),oli.OLD_LEND_TIME,i.LEND_TIME) <= DATE_FORMAT('2017-11-30', "%Y-%m-%d 23:59:59")

#### 分析后：
    ALTER TABLE settle_info ADD INDEX IDX_SI_OVERDUE_ID(OVERDUE_ID) 
    ALTER TABLE overdue_info ADD INDEX REPAY_ID(REPAY_ID)
    
    原来执行时间4S   现在  0.479s

### 6、

    SELECT 
      s.MORTGAGE_TYPE,
      IF(
        (
          s.PRODUCT_TYPE = 4 || s.PRODUCT_TYPE = 6 || s.PRODUCT_TYPE = 10 || s.PRODUCT_TYPE = 11
        ),
        oli.OLD_LOAN_TERM,
        s.LOAN_TERM
      ) AS LOAN_TERM,
      s.TERM_TYPE,
      s.LOAN_NAME,
      IF(
        (
          s.PRODUCT_TYPE = 4 || s.PRODUCT_TYPE = 6 || s.PRODUCT_TYPE = 10 || s.PRODUCT_TYPE = 11
        ),
        oli.OLD_LOAN_AMOUNT,
        s.LOAN_AMOUNT
      ) AS LOAN_AMOUNT,
      IF(
        (
          s.PRODUCT_TYPE = 4 || s.PRODUCT_TYPE = 6 || s.PRODUCT_TYPE = 10 || s.PRODUCT_TYPE = 11
        ),
        oli.OLD_LEND_TIME,
        s.LEND_TIME
      ) AS LEND_TIME,
      s.SALESMAN_ID,
      s.SALESMAN_NAME,
      u.NAME,
      s.STORE_NAME,
      IF(
        rpn.REPAY_TYPE = 3,
        rlo.REPAY_PRINCIPAL,
        rpn.PRINCIPAL
      ) AS SHOULD_PRINCIPAL,
      IF(
        rpn.REPAY_TYPE = 3,
        rlo.INTEREST,
        rpn.INTEREST
      ) AS SHOULD_INTEREST,
      IF(
        rpn.REPAY_TYPE = 3,
        rlo.ACCOUNT_FEE,
        rpn.ACCOUNT_FEE
      ) AS ACCOUNT_FEE,
      rpn.PLATFORM_FEE,
      IF(
        rpn.REPAY_TYPE = 3,
        rlo.PLATFORM_FEE,
        rpn.MANAGE_FEE
      ) AS MANAGE_FEE,
      IF(
        rpn.REPAY_TYPE = 3,
        rlo.GPS_FEE_MONTH,
        rpn.GPS_FEE
      ) AS GPS_FEE,
      IF(
        rpn.REPAY_TYPE = 3,
        rlo.PARK_FEE_MONTH,
        rpn.PARK_FEE
      ) AS PARK_FEE_BYMONTH,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.POLI_DEPOSIT
      ) AS POLI_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.YEAR_DEPOSIT
      ) AS YEAR_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.ILLEGAL_DEPOSIT
      ) AS ILLEGAL_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.PLATE_DEPOSIT
      ) AS PLATE_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.IDCARD_DEPOSIT
      ) AS IDCARD_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.CAR_DEPOSIT
      ) AS CAR_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.BORROWER_DEPOSIT
      ) AS BORROWER_DEPOSIT,
      IF(
        rpn.REPAY_TYPE = 3,
        NULL,
        rpn.CASH_DEPOSIT
      ) AS CASH_DEPOSIT,
      rlo.DEPOSITORY_FEE,
      rlo.RISK_DEPOSIT,
      s.ACTUAL_ARRIVAL_AMOUNT,
      IFNULL(rpn.NEW_BALANCE, 0) + IFNULL(rpn.EXTRA_AMOUNT, 0) AS NEW_BALANCE,
      rpn.ACTUAL_REPAY_AMOUNT,
      rps.ACTUAL_REPAY_AMOUNT_SUM,
      s.REMAIN_BALANCE,
      rpn.REPAY_DATE,
      rpn.REPAY_TYPE,
      s.ARCHIVE_ID,
      s.LOAN_ID,
      s.GPS_FEE_TYPE,
      s.PRODUCT_ID,
      s.PRODUCT_TYPE,
      s.REPAY_TYPE_ID,
      s.LOAN_TYPE,
      rpn.IMPORT_TIME,
      rpn.REALITY_REPAY_DATE,
      rpn.TRANSACTION_NUM,
      rpn.CONFIG_TIME,
      rpn.REPAY_WAYS,
      rpn.REPAY_REMARK 
    FROM
      repay_plan_view rpn 
      LEFT JOIN repay_details s 
        ON rpn.REPAY_ID = s.REPAY_ID 
      LEFT JOIN SYSTEM_USER u 
        ON s.OWNER = u.SYSTEM_ID 
      LEFT JOIN 
        (SELECT 
          SUM(ACTUAL_REPAY_AMOUNT) AS ACTUAL_REPAY_AMOUNT_SUM,
          REPAY_ID 
        FROM
          repay_plan 
        WHERE STATUS != 4 
        GROUP BY REPAY_ID) rps 
        ON rps.REPAY_ID = rpn.REPAY_ID 
      LEFT JOIN old_loan_info oli 
        ON oli.LOAN_ID = s.LOAN_ID 
      LEFT JOIN renew_loan_info rlo 
        ON rpn.REPAY_PLAN_ID = rlo.REPAY_PLAN_ID 
    WHERE 1 = 1 
      AND rpn.STATUS != 4 
      AND rpn.CONFIG_TIME IS NOT NULL 
      AND rpn.REPAY_DATE >= DATE_FORMAT(
        '2017-10-30',
        "%Y-%m-%d 00:00:00"
      ) 
      AND rpn.REPAY_DATE <= DATE_FORMAT(
        '2017-11-30',
        "%Y-%m-%d 23:59:59"
      ) 
    ORDER BY rpn.REPAY_DATE ASC 
    LIMIT 0, 20 
    
#### 分析得出使用到了视图  先优化视图里面的查询 
    
    ALTER TABLE repay_line_info ADD INDEX IDX_REPAY_STATUS(REPAY_STATUS,REPAY_PLAN_ID)
    
    ALTER TABLE receivables_history ADD INDEX IDX_RH_REPAY_PLAN_ID(REPAY_PLAN_ID)
    
    ALTER TABLE renew_loan_info ADD INDEX IDX_RLI_REPAY_PLAN_ID(REPAY_PLAN_ID)
    
    
    执行时间有原来8s 降到0.43s

#### 7、

    SELECT COUNT(0)
    FROM repay_details p1
    WHERE (p1.LOAN_STATUS IN (2, 3, 4)
    		OR (p1.LOAN_STATUS IN (9, 10, 11)
    			AND (p1.TOTAL_BALANCE > 0
    				OR p1.PRODUCT_STATE = 1
    				AND p1.REPAY_TYPE_ID != 2
    				AND (
    					SELECT COUNT(addit_borrow_fee.ADDID_FEE_ID)
    					FROM addit_borrow_fee 					WHERE addit_borrow_fee.REPAY_ID = p1.REPAY_ID
    						AND addit_borrow_fee.IS_REPAY = 2
    						AND addit_borrow_fee.REPAY_STATUS IN (1, 2, 4)
    						AND p1.LOAN_STATUS IN (9, 10)
    						AND addit_borrow_fee.PARAMETER_CODE = 'poliDeposit'
    				) > 0)))
    	AND p1.REPAY_ID NOT IN (
    		SELECT p2.REPAY_ID
    		FROM renew_loan_info p2
    		WHERE p2.AUDIT_RESULT = 1
    	) 

#### 分析修改：
    ALTER TABLE renew_loan_info ADD INDEX IDX_RLI_AUDIT_RESULT(AUDIT_RESULT)
    
    ALTER TABLE addit_borrow_fee ADD INDEX IDX_ABF_REPAY_ID(REPAY_ID,IS_REPAY,REPAY_STATUS,PARAMETER_CODE)
    
    由原来1.14s 到0.15s


### 优化时间：11.30 16:41:00 优化完成  可以看之后的时间段慢sql 